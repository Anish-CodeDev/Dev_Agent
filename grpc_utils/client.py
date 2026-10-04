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
                if res is None:
                    return "Failure"
                return res.status
            except Exception as e:
                print("An error occurred:",str(e))
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
                print(res.status)
                if res is  None:
                    return "Failure"

                return res.status
            except Exception as e:
                print("An error occurred:",str(e))
                return "Failure"
    else:
        return "Incorrect data format provided by agent"

def viewFiles(app_name,file_name):
    with grpc.insecure_channel("localhost:9000") as channel:
        stub = config_pb2_grpc.ManageAgentOpsStub(channel)
        try:
            res = stub.ViewFile(
                config_pb2.ViewFileRequest(path=file_name,app_name=app_name)
            )
            print(res)
            if res is None:
                return "Failure"

            return res.code
        except Exception as e:
            print("An error occurred:",str(e))
            return "Failure"
if __name__ == "__main__":
    #executeCommands(['echo "hey there"'],'test',False)
    viewFiles('test','a.py')