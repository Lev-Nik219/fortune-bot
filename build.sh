@"
#!/bin/bash
pip install --upgrade pip
pip install -r requirements.txt
"@ | Out-File -FilePath build.sh -Encoding UTF8