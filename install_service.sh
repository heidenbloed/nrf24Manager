echo "Stop service"
sudo systemctl stop nrf24_manager.service
if [ ! -f venv/bin/activate ]; then
  echo "Install virtual python environment"
  python3.8 -m venv venv
fi
source venv/bin/activate
echo "Install python requirements"
pip install -r ./requirements.txt
echo "Copy service"
sudo cp nrf24_manager.service /etc/systemd/system/
echo "Adapt service for current user"
sudo sed -i "s@USERNAME@$USER@" /etc/systemd/system/nrf24_manager.service
sudo sed -i "s@HOMEDIR@$HOME@" /etc/systemd/system/nrf24_manager.service
echo "Enable service"
sudo systemctl enable nrf24_manager.service
echo "Start service"
sudo systemctl start nrf24_manager.service
echo "Status of service"
sudo systemctl status nrf24_manager.service