import subprocess
import sys

cmd = [
    r"C:\Users\Administrator\.workbuddy\binaries\node\cli-connector-packages\dws.cmd",
    "chat", "message", "send",
    "--group", "cidnfDzVFUHwP081h7ClA2d5TeeCo4WhclfZq8EDsrHlUI=",
    "--msg-type", "file",
    "--dentry-id", "226656320478",
    "--space-id", "6408419582",
    "--file-name", "four_agents.jpg",
    "--file-type", "jpg",
    "--file-path", r"d:\Zero Tools\four_agents.jpg",
    "--file-size", "1097835",
    "--title", "four_agents.jpg",
    "-y",
    "--format", "json",
    "--debug"
]

print("Running command...")
sys.stdout.flush()
proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)

# Read stdout line by line
while True:
    line = proc.stdout.readline()
    if not line:
        break
    print("STDOUT:", line, end="")
    sys.stdout.flush()

while True:
    line = proc.stderr.readline()
    if not line:
        break
    print("STDERR:", line, end="")
    sys.stdout.flush()

proc.wait()
print(f"Process finished with code {proc.returncode}")
