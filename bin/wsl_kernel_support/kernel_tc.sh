#!/bin/bash
if [ -z "$CUR_USER" ]; then
  echo "CUR_USER environment variable not set, please set it as follows:"
  echo "sudo CUR_USER=\$USER ./tc_enable.sh"
  exit
fi

echo "download dependencies"
apt update -y && apt install -y build-essential flex bison dwarves libssl-dev libelf-dev 2>&1 > /dev/null

echo "download $target_tar"
wsl_kernel_ver="6.6.36.6"
target_tar="linux-msft-wsl-$wsl_kernel_ver.tar.gz"
extracted_dir="WSL2-Linux-Kernel-linux-msft-wsl-$wsl_kernel_ver"
wget "https://github.com/microsoft/WSL2-Linux-Kernel/archive/refs/tags/$target_tar" > /dev/null
echo "extract $target_tar"
tar xf "$target_tar"
cd $extracted_dir

arch="$1"
if [ -z "$1" ]; then
  arch="x86"
  echo "arch not provided, use default: x86"
fi
config_path="./arch/$arch/configs/config-wsl"
ls -l "$config_path" > /dev/null
if [ "$?" -ne 0 ]; then
  echo "File not found"
  exit
fi
echo "config-wsl found"

echo "update wsl-config"
declare -A tc_options=(
["CONFIG_NET_SCHED"]="y"
["CONFIG_NET_SCH_CBQ"]="m"
["CONFIG_NET_SCH_HTB"]="m"
["CONFIG_NET_SCH_CSZ"]="m"
["CONFIG_NET_SCH_PRIO"]="m"
["CONFIG_NET_SCH_RED"]="m"
["CONFIG_NET_SCH_SFQ"]="m"
["CONFIG_NET_SCH_TEQL"]="m"
["CONFIG_NET_SCH_TBF"]="m"
["CONFIG_NET_SCH_GRED"]="m"
["CONFIG_NET_SCH_DSMARK"]="m"
["CONFIG_NET_SCH_INGRESS"]="m"
["CONFIG_NET_SCH_NETEM"]="y"
["CONFIG_NET_QOS"]="y"
["CONFIG_NET_ESTIMATOR"]="y"
["CONFIG_NET_CLS"]="y"
["CONFIG_NET_CLS_TCINDEX"]="m"
["CONFIG_NET_CLS_ROUTE4"]="m"
["CONFIG_NET_CLS_ROUTE"]="y"
["CONFIG_NET_CLS_FW"]="m"
["CONFIG_NET_CLS_U32"]="m"
["CONFIG_NET_CLS_RSVP"]="m"
["CONFIG_NET_CLS_RSVP6"]="m"
["CONFIG_NET_CLS_POLICE"]="y"
)
for key in "${!tc_options[@]}"; do
  sed -i -e "/# $key is not set/d" "$config_path"
  sed -i -e "/$key=/d" "$config_path"
  echo "$key=${tc_options[$key]}" >> "$config_path"
done
echo "updated wsl config: $config_path"

echo "run make command with updated wsl config path"
echo | make -j$(nproc) KCONFIG_CONFIG=$config_path
echo "finished kernel make"

make modules_install headers_install
echo "finished modules_install headers_install"

home_dir=/mnt/c/Users/$CUR_USER
rm -f $home_dir/.wslconfig $home_dir/vmlinux

cp vmlinux $home_dir
echo "copied vmlinux to home dir"

cd - > /dev/null
rm -rf $target_tar $extracted_dir

echo "[wsl2]
kernel = C:\\\\Users\\\\$CUR_USER\\\\vmlinux" > $home_dir/.wslconfig
echo "created .wslconfig in home dir"
echo "Please reboot wsl now"
