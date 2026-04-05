import subprocess
class CLI:
    def __init__(self,command):
        self.command = command
    def run_command(self):
        process = subprocess.Popen(
            self.command,
            shell=True,
            stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )

        for line in process.stdout:
            print(line,end='')
        process.wait()

if __name__ == "__main__":
    cli = CLI("dir")
    cli.run_command()