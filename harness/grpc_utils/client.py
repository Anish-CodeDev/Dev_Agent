import json
import grpc
import grpc_utils.config_pb2 as config_pb2
import grpc_utils.config_pb2_grpc as config_pb2_grpc

SERVICE_CONFIG = json.dumps({"loadBalancingConfig": [{"round_robin": {}}]})

# 1. Use triple slashes ('dns:///') and keep the channel persistent
channel = grpc.insecure_channel(
    "dns:///dev-agent-service:9000",
    options=[("grpc.service_config", SERVICE_CONFIG)]
)
stub = config_pb2_grpc.ManageAgentOpsStub(channel)

def createFiles(files, contents, name):
    if isinstance(files, list) and isinstance(contents, list) and isinstance(name, str):
        try:
            res = stub.CreateFiles(
                config_pb2.CreateFileRequest(files=files, contents=contents, app_name=name)
            )
            return res.status if res else "Failure"
        except Exception as e:
            print("An error occurred:", str(e))
            return "Failure"
    else:
        raise TypeError("Incorrect format provided")

def executeCommands(cmds, name, load_from_file):
    if isinstance(cmds, list) and isinstance(name, str) and isinstance(load_from_file, bool):
        try:
            res = stub.ExecuteCommands(
                config_pb2.ExecuteCommandsRequest(cmds=cmds, app_name=name, load_from_file=load_from_file)
            )
            return res.status if res else "Failure"
        except Exception as e:
            print("An error occurred:", str(e))
            return "Failure"
    else:
        return "Incorrect data format provided by agent"

def viewFiles(app_name, file_name):
    try:
        res = stub.ViewFile(
            config_pb2.ViewFileRequest(path=file_name, app_name=app_name)
        )
        return res.code if res else "Failure"
    except Exception as e:
        print("An error occurred:", str(e))
        return "Failure"