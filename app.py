from flask import Flask, render_template, request
import paramiko
import time

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/deploy', methods=['POST'])
def deploy():
    ssh_host = request.remote_addr
    ssh_username = request.form['username']
    ssh_password = request.form['password']

    # Connect to the SSH server
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(ssh_host, username=ssh_username, password=ssh_password)

    if 'setup' in request.form:
        # Install Docker using sudo
        _, stderr, _ = ssh.exec_command(f'echo {ssh_password} | sudo -S apt update')
        exit_status = stderr.channel.recv_exit_status()
        if exit_status != 0:
            return render_template('index.html', error_message='Deployment failed! Error in apt update.')

        # Install Docker using sudo
        _, stderr, _ = ssh.exec_command(f'echo {ssh_password} | sudo -S apt install -y git nginx')
        exit_status = stderr.channel.recv_exit_status()
        if exit_status != 0:
            return render_template('index.html', error_message='Deployment failed! Error in installing git or nginx.')

        # Check if the SOC-Build directory exists
        _, stdout, _ = ssh.exec_command('ls SOC-Build')
        directory_exists = len(stdout.read().decode('utf-8').strip()) > 0

        if not directory_exists:
            # Clone the GitHub repository
            _, stderr, _ = ssh.exec_command(f'echo {ssh_password} | sudo -S git clone https://github.com/akabigsmokee/SOC-Build.git')
            exit_status = stderr.channel.recv_exit_status()
            if exit_status != 0:
                return render_template('index.html', error_message='Deployment failed! Error in cloning the repository.')


        # Execute commands as the superuser
        _, stderr, _ = ssh.exec_command(f'echo {ssh_password} | sudo -S su')
        exit_status = stderr.channel.recv_exit_status()
        if exit_status != 0:
            return render_template('index.html', error_message='Deployment failed! Error in executing commands as superuser.')

        # Install Docker using sudo
        _, stderr, _ = ssh.exec_command(f'echo {ssh_password} | sudo -S apt update')
        exit_status = stderr.channel.recv_exit_status()
        if exit_status != 0:
            return render_template('index.html', error_message='Deployment failed! Error in installing Docker.')

        _, stderr, _ = ssh.exec_command(f'echo {ssh_password} | sudo -S apt install -y docker.io')
        exit_status = stderr.channel.recv_exit_status()
        if exit_status != 0:
            return render_template('index.html', error_message='Deployment failed! Error in installing Docker.')
        # Install Docker Compose using sudo
        _, stderr, _ = ssh.exec_command(f'echo {ssh_password} | sudo -S apt install -y docker-compose')
        exit_status = stderr.channel.recv_exit_status()
        if exit_status != 0:
            return render_template('index.html', error_message='Deployment failed! Error in installing Docker Compose.')

        # Generate SSL certificate and key using openssl
        _, stderr, _ = ssh.exec_command(f'echo {ssh_password} | sudo -S mkdir -p /etc/nginx/ssl')
        exit_status = stderr.channel.recv_exit_status()
        if exit_status != 0:
            return render_template('index.html', error_message='Deployment failed! Error in creating certificate directory.')

        _, stderr, _ = ssh.exec_command(f'echo {ssh_password} | sudo -S openssl req -new -newkey rsa:2048 -days 365 -nodes -x509 -subj "/CN=Techso-Group" -keyout /etc/nginx/ssl/private-key.pem -out /etc/nginx/ssl/certificate.pem')
        exit_status = stderr.channel.recv_exit_status()
        if exit_status != 0:
            return render_template('index.html', error_message='Deployment failed! Error in generating SSL certificate and key.')

        return render_template('index.html', status_message='Environment setup completed!', environment_setup_completed=True)
    
    elif 'compose' in request.form:

        # Change to the repository directory
        _, stderr, _ = ssh.exec_command('cd SOC-Build')
        exit_status = stderr.channel.recv_exit_status()
        if exit_status != 0:
            return render_template('index.html', error_message='Deployment failed! Error in changing to the repository directory.')

        # Change to the repository directory
        _, stderr, _ = ssh.exec_command(f'cp /home/{ssh_username}/SOC-Build/docker-compose.yml /home/{ssh_username}/')
        exit_status = stderr.channel.recv_exit_status()
        if exit_status != 0:
           return render_template('index.html', error_message='Deployment failed! Error in copying composer to the repository directory.')

        # Change to the repository directory
        _, stderr, _ = ssh.exec_command(f'cp /home/{ssh_username}/SOC-Build/application.conf /home/{ssh_username}/')
        exit_status = stderr.channel.recv_exit_status()
        if exit_status != 0:
           return render_template('index.html', error_message='Deployment failed! Error in copying app conf to the repository directory.')

        # Change to the repository directory
        _, stderr, _ = ssh.exec_command(f'echo {ssh_password} | sudo -S rm -r /var/www/html')
        exit_status = stderr.channel.recv_exit_status()
        if exit_status != 0:
           return render_template('index.html', error_message='html folder not removed.')          
        
        # Change to the repository directory
        _, stderr, _ = ssh.exec_command(f'echo {ssh_password} | sudo -S cp -r /home/{ssh_username}/SOC-Build/html /var/www/')
        exit_status = stderr.channel.recv_exit_status()
        if exit_status != 0:
           return render_template('index.html', error_message='Deployment failed! Error in copying html folder to the repository directory.')

        # Change to the repository directory
        _, stderr, _ = ssh.exec_command(f'echo {ssh_password} | sudo -S rm /etc/nginx/sites-enabled/default')
        exit_status = stderr.channel.recv_exit_status()
        if exit_status != 0:
           return render_template('index.html', error_message='default file not removed.') 

        # Change to the repository directory
        _, stderr, _ = ssh.exec_command(f'echo {ssh_password} | sudo -S cp /home/{ssh_username}/SOC-Build/services /etc/nginx/sites-available/')
        exit_status = stderr.channel.recv_exit_status()
        if exit_status != 0:
           return render_template('index.html', error_message='Deployment failed! Error in copying services conf to the repository directory.')                 
        
        # Change to the repository directory
        _, stderr, _ = ssh.exec_command(f'echo {ssh_password} | sudo -S ln -s /etc/nginx/sites-available/services /etc/nginx/sites-enabled/')
        exit_status = stderr.channel.recv_exit_status()
        if exit_status != 0:
           return render_template('index.html', error_message='Deployment failed! Error in copying services conf to the repository directory.')          

        # Change to the repository directory
        _, stderr, _ = ssh.exec_command(f'echo {ssh_password} | sudo -S systemctl restart nginx')
        exit_status = stderr.channel.recv_exit_status()
        if exit_status != 0:
           return render_template('index.html', error_message='cant restart nginx')          
        
        # Execute the docker-compose up command
        ssh.exec_command(f'echo {ssh_password} | sudo -S nohup docker-compose up > /dev/null 2>&1 &')

          # Check if docker-compose is running
        docker_compose_pid = None

        while not docker_compose_pid:
            time.sleep(5)  # Wait for 5 seconds before checking again

            _, stdout, _ = ssh.exec_command('pgrep docker-compose')
            docker_compose_pid = stdout.read().decode('utf-8').strip()

        return render_template('index.html', status_message='Please wait for 15 minutes...', environment_setup_completed=True, compose_button_disabled=True)

    return render_template('index.html', environment_setup_completed=False)  # Render the initial page if no button is clicked

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
