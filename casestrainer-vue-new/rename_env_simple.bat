@echo off
echo Renaming environment files...

if exist "_env" (
    if exist ".env" (
        echo Backing up existing .env to .env.bak
        move /Y ".env" ".env.bak"
    )
    echo Renaming _env to .env
    move /Y "_env" ".env"
)

if exist "_env.development" (
    if exist ".env.development" (
        echo Backing up existing .env.development to .env.development.bak
        move /Y ".env.development" ".env.development.bak"
    )
    echo Renaming _env.development to .env.development
    move /Y "_env.development" ".env.development"
)

if exist "_env.production" (
    if exist ".env.production" (
        echo Backing up existing .env.production to .env.production.bak
        move /Y ".env.production" ".env.production.bak"
    )
    echo Renaming _env.production to .env.production
    move /Y "_env.production" ".env.production"
)

if exist "_env.example" (
    if exist ".env.example" (
        echo Backing up existing .env.example to .env.example.bak
        move /Y ".env.example" ".env.example.bak"
    )
    echo Renaming _env.example to .env.example
    move /Y "_env.example" ".env.example"
)

echo.
echo Environment files have been renamed successfully!
echo You can now start your development server.
pause
