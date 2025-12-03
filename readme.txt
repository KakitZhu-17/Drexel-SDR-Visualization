1.get wsl to run on vscode use this command: wsl --install
(there will be some setup stuff like username and password)
2.install ubuntu 20.04 (get from microsoft store or ubuntu releases)
4.go into vscode and connect to WSL using distro to select 20.04
3.on terminal use this command:
    git clone --recursive -b wip/radiowars2024 https://github.com/drexelwireless/dragonradio.git
4.once files are done cloning, cd into dragonradio and run the setup.py file with thsi command: python setup.py install
(you can use venv (), it probably reccomended anyway heres the command: sudo apt install -y python3-virtualenv virtualenv , make sure sudo is actually installed before running this)
5.that should get you the dragonradio library to run decompressIQData and the app itself
NOTE: you may need to reinstall some libraries like numpy, scipy, pyqt5, pyqtgraph
