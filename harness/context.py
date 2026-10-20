import json
from pathlib import Path
import os
from mongodb import DBOps
CONTEXT_FILE =  Path(os.path.join("/data", "context.json"))
obj = DBOps('data')

def addContext(app, context, files=None):
	contents = CONTEXT_FILE.read_text(encoding="utf-8") if CONTEXT_FILE.exists() else ""
	data = json.loads(contents) if contents.strip() else {"apps": []}

	app_data = next((entry[app] for entry in data["apps"] if app in entry), None)
	if app_data is None:
		app_data = {"context": [], "files": []}
		data["apps"].append({app: app_data})

	app_data.setdefault("files", [])
	app_data["context"].append(context)
	for file in files or []:
		if file not in app_data["files"]:
			app_data["files"].append(file)
	obj.update_user_data(data,'context')
	CONTEXT_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def getContext(app):
	contents = CONTEXT_FILE.read_text(encoding="utf-8") if CONTEXT_FILE.exists() else ""
	if not contents:
		contents = obj.find_documents({"type":"context"})
		for doc in contents:
			data = doc.get("data")
	else:

		data = json.loads(contents) if contents.strip() else {"apps": []}
	app_data = next((entry[app] for entry in data.get("apps", []) if app in entry), None)
	return app_data.get("context", []) if app_data else []


def getFiles(app_name):
	contents = CONTEXT_FILE.read_text(encoding="utf-8") if CONTEXT_FILE.exists() else ""
	if not contents:
			contents = obj.find_documents({"type":"context"})
			for doc in contents:
				data = doc.get("data")
	else:

		data = json.loads(contents) if contents.strip() else {"apps": []}
	app_data = next((entry[app_name] for entry in data.get("apps", []) if app_name in entry), None)
	return app_data.get("files", []) if app_data else []


if __name__ == "__main__":
	addContext("restuarant-app","The frontend agent completed it's process")