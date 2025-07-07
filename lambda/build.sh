#!/usr/bin/env bash
set -euo pipefail

# directorio temporal donde instalaremos dependencias
rm -rf build && mkdir build
# copiar tu código
cp handler.py build/

# si tu lambda tiene requirements.txt, instala ahí dentro:
if [ -f requirements.txt ]; then
  pip install -r requirements.txt -t build/
fi

# crea el paquete zip usando Python
cd build
python - <<'PYCODE'
import shutil
shutil.make_archive('../lambda', 'zip', root_dir='.')
PYCODE

cd ..
rm -rf build
echo "✅ lambda.zip generado."
