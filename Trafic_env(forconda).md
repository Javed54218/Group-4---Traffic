to create the venv for the lwr library you need jupyter notebook
you need to run the following:
conda create -n traffic_env python=3.11
conda activate traffic_env
conda install numpy matplotlib ipywidgets jupyterlab
conda install -c conda-forge ipywidgets
conda install notebook ipykernel
conda install ipython
 this should setup jupyter correctly for use 
 the code does also require custom libraries made by this guy from UW:
 https://faculty.washington.edu/rjl/ - link to website
 https://github.com/clawpack/riemann_book?utm_source=chatgpt.com -link to github repository
