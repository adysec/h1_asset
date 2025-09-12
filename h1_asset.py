import requests
import json
import os

from typing import Dict, Set

# In-process cache to avoid re-reading files repeatedly for duplicate detection
_write_cache: Dict[str, Set[str]] = {}

def write_word(word,target):
	# initialize cache for this target if needed
	if target not in _write_cache:
		lines: Set[str] = set()
		if os.path.exists(target)==True:
			with open(target,'r',encoding='utf-8')as f:
				for line in f:
					lines.add(line.rstrip('\n'))
		_write_cache[target] = lines
	# skip if already present
	if word in _write_cache[target]:
		return
	# append and update cache
	with open(target,'a+',encoding='utf-8')as fp:
		fp.write(word+'\n')
	_write_cache[target].add(word)

def get_assets(handle):
	url = "https://hackerone.com/graphql"

	# Build cookies and headers from environment to avoid hardcoded secrets
	cookies = {}
	try:
		if os.getenv('H1_COOKIES_JSON'):
			cookies = json.loads(os.getenv('H1_COOKIES_JSON'))
		helper_session = os.getenv('H1_SESSION')
		if helper_session:
			cookies['__Host-session'] = helper_session
		helper_device = os.getenv('H1_DEVICE_ID')
		if helper_device:
			cookies['h1_device_id'] = helper_device
	except Exception as e:
		print('env cookies parse error\t'+str(e))

	headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:91.0) Gecko/20100101 Firefox/91.0", "Accept": "*/*", "Content-Type": "application/json"}
	if os.getenv('H1_X_CSRF_TOKEN'):
		headers["X-Csrf-Token"] = os.getenv('H1_X_CSRF_TOKEN')

	data = {"operationName":"TeamAssets","variables":{"handle":handle},"query":"query TeamAssets($handle: String!) {\n  me {\n    id\n    membership(team_handle: $handle) {\n      id\n      permissions\n      __typename\n    }\n    __typename\n  }\n  team(handle: $handle) {\n    id\n    handle\n    structured_scope_versions(archived: false) {\n      max_updated_at\n      __typename\n    }\n    in_scope_assets: structured_scopes(first: 650, archived: false, eligible_for_submission: true) {\n      edges {\n        node {\n          id\n          asset_type\n          asset_identifier\n          instruction\n          max_severity\n          eligible_for_bounty\n          labels(first: 100) {\n            edges {\n              node {\n                id\n                name\n                __typename\n              }\n              __typename\n            }\n            __typename\n          }\n          __typename\n        }\n        __typename\n      }\n      __typename\n    }\n    out_scope_assets: structured_scopes(first: 650, archived: false, eligible_for_submission: false) {\n      edges {\n        node {\n          id\n          asset_type\n          asset_identifier\n          instruction\n          __typename\n        }\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n}\n"}

	try:
		r = requests.post(url, headers=headers, cookies=cookies, json=data, timeout=20)
		if r.status_code != 200:
			print(handle+'\tgraphql status '+str(r.status_code))
			return
		try:
			response = r.json()
		except ValueError:
			print(handle+'\tgraphql json error')
			return
		for i in response.get('data',{}).get('team',{}).get('in_scope_assets',{}).get('edges', []):
			write_word(i['node']['asset_identifier'],'src/'+handle+'/'+i['node']['asset_type']+'.txt')
			write_word(i['node']['asset_identifier'],'src/'+i['node']['asset_type']+'.txt')
	except Exception as e:
		print(handle+'\terror\t'+str(e))

page = 0
while True:
	page = page + 1
	try:
		res = requests.get('https://hackerone.com/programs/search?query=type:hackerone&sort=published_at:descending&page='+str(page), timeout=20)
		if res.status_code != 200:
			break
		try:
			res_json = res.json()
		except ValueError:
			break
		results = res_json.get('results', [])
		if not results:
			break
		for i in results:
			word = str(i['id'])+'\t'+'https://hackerone.com'+i['url']+'\t'+i['name']+'\t'+i['handle']
			url = 'https://hackerone.com'+i['url']
			name = i['name']
			handle = i['handle']
			#建目录
			if not os.path.exists('src/'+handle):
				os.mkdir('src/'+handle)
			write_word(word,'src/'+handle+'/note.txt')
			write_word(word,'src/note.txt')
			try:
				get_assets(handle)
			except Exception as e:
				print(handle+'\terror\t'+str(e))
	except Exception:
		break
