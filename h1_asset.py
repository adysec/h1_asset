import requests
import json
import os

from typing import Dict, Set

# In-process cache to avoid re-reading files repeatedly for duplicate detection
_write_cache: Dict[str, Set[str]] = {}

# Default inline configuration (filled here instead of secrets manager)
H1_DEFAULT_COOKIES = {"h1_device_id": "6b006754-624f-48dd-8640-3a6c1b2594a5", "_gcl_au": "1.1.11592276.1653657152", "_ga": "GA1.2.1701425692.1653657219", "amp_b7cba2": "LtSVdSlcq8x09-wpdce0ud.ZTFlZmNjZWQtNjMzNy00YmFlLTlmZTctNDM1MGMwZjNmOWRj..1g42qde4b.1g42s7l4j.e.2.g", "__Host-session": "dEJBMnQwcjlwQlNnYTV3b24xUHNlRWN0Z2d6ZlhBYXdoaWlISnRHL3BsNWtmcGxMWXhQN3RVc1l6aWRIWmt6UU9YU1N6ZzN6MWY3a0xBVlFLanh4NE1jN3BFb1FZQjh4YVd3eEdmb2FUQUQ4c1N0d3N0N1phS2N5V3VJTGFadVZWSnZNSStEMGxHa3Q5NkV0NVZrWW0yelJUSmIveWNIQTQxUHNtRzVwR2pQcTNCMHg0NEJNYy9aaVJvblcxRU9PRU1vRXlFMllVcTF5bVBIUFN6Y2pKTTdRakttdVhwTmdrVUw1UW43UXIvc0czZmFhYlY4MzFCTVBxSld1ZFlseU9HZ3BTcHU3Y3VVQVpTMk5QbWFoS3JlUjhtTDJxQ2Vya0c1VmRJbFlpTjNybkdqQ0dTT0lTRGpNRlRQVTB4cjM3aFR0L3JqVHZrUEJBaDBSRUNiOFJBPT0tLVhBdlpUM2Y5dnNucG5QRjhKM3dsT3c9PQ%3D%3D--2241d124b675695c0d174cae11d3e0fabb59b119", "_dd_s": "rum=0&expire=1660822945246", "AMP_b7cba2c14c": "JTdCJTIyb3B0T3V0JTIyJTNBZmFsc2UlMkMlMjJkZXZpY2VJZCUyMiUzQSUyMkx0U1ZkU2xjcTh4MDktd3BkY2UwdWQlMjIlMkMlMjJsYXN0RXZlbnRUaW1lJTIyJTNBMTY2MDgyMjA0NjA0MiUyQyUyMnNlc3Npb25JZCUyMiUzQTE2NjA4MjE0NzEzNjglMkMlMjJ1c2VySWQlMjIlM0ElMjJlMWVmY2NlZC02MzM3LTRiYWUtOWZlNy00MzUwYzBmM2Y5ZGMlMjIlN0Q=", "_gid": "GA1.2.1018576083.1660821473", "AMP_MKTG_b7cba2c14c": "JTdCJTdE"}
H1_DEFAULT_X_CSRF_TOKEN = "QOFiIvQ7XJceEJ/y7Z5M1KO9CcO6PBehaUSTQmgdpE33/ZSAIWNNVzBJzf8bH7d1Ynw9VKj6mesrZ2BUdfQF7Q=="

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

	# Build cookies and headers from in-script defaults only
	cookies = dict(H1_DEFAULT_COOKIES) if isinstance(H1_DEFAULT_COOKIES, dict) else {}

	headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:91.0) Gecko/20100101 Firefox/91.0", "Accept": "*/*", "Accept-Language": "zh-CN,zh-TW;q=0.8,en-US;q=0.5,en;q=0.3", "Accept-Encoding": "gzip, deflate", "Referer": "https://hackerone.com/cornershop?type=team", "Content-Type": "application/json", "Origin": "https://hackerone.com", "Sec-Fetch-Dest": "empty", "Sec-Fetch-Mode": "cors", "Sec-Fetch-Site": "same-origin", "Te": "trailers"}
	if H1_DEFAULT_X_CSRF_TOKEN:
		headers["X-Csrf-Token"] = H1_DEFAULT_X_CSRF_TOKEN

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
