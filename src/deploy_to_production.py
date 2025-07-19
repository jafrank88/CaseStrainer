#!/usr/bin/env python
"""
Deployment script for CaseStrainer
Copies the necessary files to the production server and restarts the application
"""
import os
import subprocess
import shutil
import argparse
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Production server details
PRODUCTION_SERVER = "wolf.law.uw.edu"
PRODUCTION_PATH = "/var/www/casestrainer"  # Adjust this path as needed


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Deploy CaseStrainer to production")
    parser.add_argument(
        "--restart",
        action="store_true",
        help="Restart the application after deployment",
    )
    return parser.parse_args()


def deploy_files():
    """Deploy the necessary files to the production server."""
    logger.info("Deploying files to production server...")

    # Files to deploy
    files_to_deploy = [
        "app_final.py",
        "templates/fixed_form_ajax.html",
        "static/js/multitool_confirmed.js",
    ]

    # Create a temporary directory for deployment files
    temp_dir = "deployment_temp"
    os.makedirs(temp_dir, exist_ok=True)

    # Copy files to temporary directory
    for file_path in files_to_deploy:
        source_path = os.path.join(os.getcwd(), file_path)
        target_dir = os.path.join(temp_dir, os.path.dirname(file_path))
        os.makedirs(target_dir, exist_ok=True)

        if os.path.exists(source_path):
            shutil.copy2(source_path, os.path.join(temp_dir, file_path))
            logger.info(f"Copied {file_path} to deployment package")
        else:
            logger.warning(f"Warning: {file_path} not found")

    # Create a deployment package
    deployment_zip = "casestrainer_deployment.zip"
    shutil.make_archive("casestrainer_deployment", "zip", temp_dir)
    logger.info(f"Created deployment package: {deployment_zip}")

    # Copy the deployment package to the production server
    try:
        # Use SCP to copy the file to the production server
        scp_args = ["scp", deployment_zip, f"{PRODUCTION_SERVER}:{PRODUCTION_PATH}"]
        logger.info(f"Running: {' '.join(scp_args)}")
        subprocess.run(scp_args, check=True)

        # Extract the deployment package on the production server
        ssh_extract_args = ["ssh", PRODUCTION_SERVER, f"cd {PRODUCTION_PATH} && unzip -o {deployment_zip}"]
        logger.info(f"Running: {' '.join(ssh_extract_args)}")
        subprocess.run(ssh_extract_args, check=True)

        logger.info("Deployment completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Error deploying files: {e}")
        return False
    finally:
        # Clean up temporary files
        if os.path.exists(deployment_zip):
            os.remove(deployment_zip)
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)


def restart_application():
    """Restart the CaseStrainer application on the production server."""
    logger.info("Restarting CaseStrainer application...")

    try:
        # SSH into the production server and restart the application
        restart_args = ["ssh", PRODUCTION_SERVER, f"cd {PRODUCTION_PATH} && python run_production.py --host 0.0.0.0 --port 5000 &"]
        logger.info(f"Running: {' '.join(restart_args)}")
        subprocess.run(restart_args, check=True)

        logger.info("Application restarted successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Error restarting application: {e}")
        return False


def main():
    """Main function to deploy CaseStrainer to production."""
    args = parse_arguments()

    # Deploy files
    deployment_success = deploy_files()

    # Restart application if requested and deployment was successful
    if args.restart and deployment_success:
        restart_application()

    logger.info("Deployment process completed")


if __name__ == "__main__":
    main()
