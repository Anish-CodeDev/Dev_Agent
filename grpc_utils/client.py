import grpc
import grpc_utils.config_pb2 as config_pb2
import grpc_utils.config_pb2_grpc as config_pb2_grpc

def createFiles(files,contents,name):
    if(isinstance(files,list) and isinstance(contents,list) and isinstance(name,str)):

        with grpc.insecure_channel("localhost:9000") as channel:
            stub = config_pb2_grpc.ManageAgentOpsStub(channel)
            try:
                res = stub.CreateFiles(
                    config_pb2.CreateFileRequest(files=files,contents=contents,app_name=name)
                )
                print(res)
                return "Success"
            except Exception as e:
                return "Failure"
    else:
        raise TypeError("Incorrect format provided")

def executeCommands(cmds,name,load_from_file):
    if(isinstance(cmds,list) and isinstance(name,str) and isinstance(load_from_file,bool)):

        with grpc.insecure_channel("localhost:9000") as channel:
            stub = config_pb2_grpc.ManageAgentOpsStub(channel)
            try:
                res = stub.ExecuteCommands(
                    config_pb2.ExecuteCommandsRequest(cmds=cmds,app_name=name,load_from_file=load_from_file)
                )
                print(res)

            except Exception as e:
                print("An error occurred:",str(e))
    else:
        raise TypeError("Incorrect format provided")

if __name__ == "__main__":
    executeCommands(['echo "hey there"'],'test',False)