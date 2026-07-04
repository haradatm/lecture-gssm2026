TOOLS=`pwd`/tools
INSTALL_ROOT="${TOOLS}/usr/local"
mkdir -p ${TOOLS}/src
mkdir -p ${INSTALL_ROOT}

export PATH=$PATH:${TOOLS}/usr/local/bin
export CPATH=$CPATH:${TOOLS}/usr/local/include
export LIBRARY_PATH=$LIBRARY_PATH:${TOOLS}/usr/local/lib

if [ -d "${INSTALL_ROOT}/lib/cabocha" ]; then
  echo "Note: cabocha is already installed."
  exit 1
fi

### Install CRF++-

cd ${TOOLS}/src
FILE_ID="12G-tRUUT1rEJ9AYyOsF5K8e7x7joJJSo"
gdown ${FILE_ID}
tar zxvf CRF++-0.58.tar.gz
cd CRF++-0.58
# wget -O config.guess 'https://git.savannah.gnu.org/cgit/config.git/plain/config.guess'
# wget -O config.sub 'https://git.savannah.gnu.org/cgit/config.git/plain/config.sub'
chmod +x config.guess config.sub
./configure --prefix=${INSTALL_ROOT}
make
make check
make install

### Install Cabocha

mkdir -p ${TOOLS}/src
cd ${TOOLS}/src
FILE_ID="1S147wx67tPtSpGYafbIYUH_NjV1dzAdb"
gdown ${FILE_ID}
tar -xvf cabocha-0.69.tar.bz2
cd cabocha-0.69
# wget -O config.guess 'https://git.savannah.gnu.org/cgit/config.git/plain/config.guess'
# wget -O config.sub 'https://git.savannah.gnu.org/cgit/config.git/plain/config.sub'
chmod +x config.guess config.sub
./configure --prefix=${INSTALL_ROOT} --with-mecab-config=${MECAB_ROOT}/bin/mecab-config --with-charset=utf8 --enable-utf8-only
make
make check
make install

cd python
# uv pip install -e .
pip install -e .
cd /usr/local/lib
sudo ln -s ${INSTALL_ROOT}/lib/libcabocha.so.5.0.0 ./libcabocha.so.5
sudo ldconfig /usr/local/lib > /dev/null 2>&1
