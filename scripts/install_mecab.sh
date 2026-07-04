TOOLS=`pwd`/tools
INSTALL_ROOT="${TOOLS}/usr/local"
mkdir -p ${TOOLS}/src
mkdir -p ${INSTALL_ROOT}

export PATH=$PATH:${TOOLS}/usr/local/bin
export CPATH=$CPATH:${TOOLS}/usr/local/include
export LIBRARY_PATH=$LIBRARY_PATH:${TOOLS}/usr/local/lib

if [ -d "${INSTALL_ROOT}/lib/mecab" ]; then
  echo "Note: mecab is already installed."
  exit 1
fi

### Install MeCab

cd ${TOOLS}/src
git clone https://github.com/taku910/mecab
cd mecab/mecab
# wget -O config.guess 'https://git.savannah.gnu.org/cgit/config.git/plain/config.guess'
# wget -O config.sub 'https://git.savannah.gnu.org/cgit/config.git/plain/config.sub'
chmod +x config.guess config.sub
./configure --with-charset=utf8 --prefix=${INSTALL_ROOT}
make
make check
make install

### Install MeCab IPADIC

cd ${TOOLS}/src/mecab/mecab-ipadic
# wget -O config.guess 'https://git.savannah.gnu.org/cgit/config.git/plain/config.guess'
# wget -O config.sub 'https://git.savannah.gnu.org/cgit/config.git/plain/config.sub'
chmod +x config.guess config.sub
./configure --with-charset=utf8 --prefix=${INSTALL_ROOT} --with-mecab-config=${INSTALL_ROOT}/bin/mecab-config
make
make install

echo '"湯畑",-1,-1,1,名詞,一般,*,*,*,*,湯畑,ユバタケ,ユバタケ,USER"' > ${INSTALL_ROOT}/lib/mecab/dic/ipadic/user_dic.csv
echo "userdic = ${INSTALL_ROOT}/lib/mecab/dic/ipadic/user.dic" >> ${INSTALL_ROOT}/etc/mecabrc
${INSTALL_ROOT}/libexec/mecab/mecab-dict-index -d ${INSTALL_ROOT}/lib/mecab/dic/ipadic -u ${INSTALL_ROOT}/lib/mecab/dic/ipadic/user.dic -f utf-8 -t utf-8 ${INSTALL_ROOT}/lib/mecab/dic/ipadic/user_dic.csv

cd ${TOOLS}/src/mecab/mecab/python
sed -i".org" -e "s/return string.split (cmd1(str))/return cmd1(str).split()/g" setup.py
python setup.py build
# uv pip install -e .
pip install -e .
cd /usr/local/lib
sudo sudo ln -s ${INSTALL_ROOT}/lib/libmecab.so.2.0.0 ./libmecab.so.2
sudo sudo ldconfig /usr/local/lib > /dev/null 2>&1
