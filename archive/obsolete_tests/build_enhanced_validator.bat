@echo off
echo Building Enhanced Validator Vue.js frontend...
cd casestrainer-vue
set PATH=D:\node;%PATH%
D:\node\npm run build
echo Build complete. Copying files to static/vue...
xcopy /E /Y dist ..\static\vue\
echo Enhanced Validator deployment complete!
