import setuptools

setuptools.setup(
    name="emscalebar",
    version="0.0.0",
    author="Albert Xu",
    author_email="albert.t.xu@gmail.com",
    description="add scale bar to electron microscopy mrc images",
    packages=setuptools.find_packages(),
    install_requires=[
        "matplotlib",
        "matplotlib-scalebar",
        "mrcfile",
        "numpy",
        "Pillow",
        "scikit-image",
    ],
    scripts=["emscalebar.py"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
