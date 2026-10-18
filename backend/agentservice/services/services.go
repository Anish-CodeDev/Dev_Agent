package services

import (
	agent "agentops/common"
	"bufio"
	"context"
	"fmt"
	"os"
	"os/exec"
	"strings"
	"path/filepath"
	"github.com/mattn/go-shellwords"
)

func runCommand(command string) (string, error) {
	if command == "" || strings.HasPrefix(command,"#"){
		return "Not Executed",nil
	}
	args, err := shellwords.Parse(command)
	cmd := exec.Command(args[0], args[1:]...)
	output, err := cmd.CombinedOutput()
	return string(output),err
}

func installFromFile(path string)(error){
	file,err:= os.Open(path)
	if err!=nil{
		return err
	}
	defer file.Close()

	scanner := bufio.NewScanner(file)

	for scanner.Scan(){
		line:=strings.TrimSpace(scanner.Text())
		out,err:= runCommand(line)
		if err!=nil{
			fmt.Println("Output: ",out)
			return err
		}
	}
	if err:=scanner.Err();err!=nil{
		return err
	}
	return nil
}
func hasFolder(p string)(bool){
	dir:=filepath.Dir(p)
	return dir!="." && dir!=string(filepath.Separator)
}
type AgentService struct {
}

func NewAgentService() *AgentService {
	return &AgentService{}
}
func (s *AgentService) ExecuteCommands(ctx context.Context, in *agent.ExecuteCommandsRequest) error {

	if err:= os.Mkdir("/data",0755);err!=nil{
		fmt.Println("Directory already exists")
	}
	res:=fmt.Sprintf("/data/%v",in.AppName)
	if err:=os.Mkdir(res,0755);err!=nil{
		fmt.Println("Directory already exists")
	}
	
	if(in.LoadFromFile){
		err:= installFromFile(res + "/commands.txt")
		return err
	}
	f, err := os.OpenFile(res+"/commands.txt", os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0644)
	if err != nil {
			return err
	}
	defer f.Close()
	for _,cmd:= range in.Cmds{
		cmd += "\n"
		data:= []byte(cmd)
		
		if(in.LoadFromFile){
		output, err:= runCommand(cmd)
		if err!=nil{
			fmt.Println("Error: ",err)
			return err
		}else{
			fmt.Println("Output: ",output)
			return nil
		}
		}
		if _,err:= f.Write(data);err!=nil{
			fmt.Println("Error: ",err)
			return err
		}
	}
	return nil
}

func (s *AgentService) CreateFiles(ctx context.Context, in *agent.CreateFileRequest) error {

	file_names := []string{}
	for _, val := range in.Files {
		file_names = append(file_names, val)
	}
	if err := os.Mkdir("/data", 0755); err != nil {
		fmt.Println("Error creating /data:", err)
	}
	res := fmt.Sprintf("/data/%v/", in.AppName)
	if err := os.Mkdir(res, 0755); err != nil {
		fmt.Println("Directory already exists")
	}
	for i, val := range in.Contents {
		data := []byte(val)
		file_name := fmt.Sprintf("/data/%v/%v", in.AppName, file_names[i])
		if(hasFolder(file_name)){
			if err:= os.Mkdir(filepath.Dir(file_name),0755); err!=nil{
				fmt.Println("Directory already exists...")
			}
		}
		err := os.WriteFile(file_name, data, 0644)
		if err != nil {
			return err
		}
	}
	
	return nil
}


func(s *AgentService) ViewFiles(ctx context.Context, in *agent.ViewFileRequest)(error,string){
fmt.Println("User wants to access the file located at ",in.Path);
data,err := os.ReadFile(fmt.Sprintf("/data/%s/%s",in.AppName,in.Path))
if err!=nil{
	return err,"Failed";
}
return nil,string(data)
}