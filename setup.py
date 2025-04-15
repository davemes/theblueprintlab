from setuptools import setup, find_packages

setup(
    name='theblueprintlab',
    version='0.1.0',
    packages=find_packages(),
    install_requires=[
        'requests',
        'python-dotenv',
        'setuptools',
        'openai',
        'datetime'
    ],
    author='David Meszaros',
    description='Automatisierung und Analyse für HubSpot und mehr',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    classifiers=[
        'Programming Language :: Python :: 3',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.8',
)