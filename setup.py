import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()
    
setuptools.setup(
    name = 'alice_blue',
    packages=setuptools.find_packages(),
    version = '0.0.2',
    include_package_data=True,
    description = 'Python library for Alice Blue APIs',
    long_description=long_description,
    long_description_content_type="text/markdown",  author = 'Krishna Velu',
    author_email = 'krishnajvelu@gmail.com',
    url = 'https://github.com/krishnavelu/alice_blue',
    install_requires=['requests', 'websocket_client', 'bs4', 'protlib'],
    keywords = ['alice', 'alice-blue', 'python', 'sdk', 'trading', 'stock markets'],
    classifiers=[
      'Intended Audience :: Developers',
      'Natural Language :: English',
      'Operating System :: OS Independent',
      'Programming Language :: Python',
      'Programming Language :: Python :: 3',
      'Programming Language :: Python :: Implementation :: PyPy',
      'Topic :: Software Development :: Libraries :: Python Modules'
    ],
)
