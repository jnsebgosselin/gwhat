Project Management in GWHAT
===============================================

This document shows how to create and open existing projects in GWHAT.
Data are managed in GWHAT by project. This means that all input and output files
relative to a particular project are stored in a common folder, hereafter referred
to as the *project folder*. This file management system allows to easily backup
or copy the data related to a particular project since all the files are saved
at the same location.

Only one project at a time can be opened per instance of GWHAT. The title of the 
currently opened project is displayed on a button located in the `project toolbar`
as shown in :numref:`project_toolbar`. The project named *Example* is opened by
default the first time GWHAT is started. This project includes samples of
files to test the different features of GWHAT.

.. _project_toolbar:
.. figure:: img/scs_project_toolbar_annoted.*
    :align: center
    :width: 100%
    :alt: alternate text
    :figclass: align-center
    
    Presentation of the project toolbar in GWHAT.

Creating a new project
-----------------------------------------------

New projects are created by clicking on the |new_project| icon located on the
project toolbar (see :numref:`project_toolbar`). This opens a dialog window 
(see :numref:`create_new_project`) where information about the project can 
be entered such as its title, author, and location coordinates.

.. _create_new_project:
.. figure:: img/scs_new_project_annoted.*
    :align: center
    :width: 100%
    :alt: alternate text
    :figclass: align-center

Clicking on the button ``Save`` will create a new *project folder*, named after
the project’s title. Moreover, information related to the project are saved
in a file with an extension *.gwt*. The directory where the *project folder* is
created can be changed by clicking the |folder| icon.

Opening an existing project
-----------------------------------------------

Clicking on the button where is displayed the currently opened project title on
the project toolbar (see  :numref:`project_toolbar`) opens a dialog window where
an existing project file (.gwt) can be selected and opened.

The path to the currently project folder is stored in a relative format. This means
that if the location of the project folder is changed relative the executable of
the software (*GWHAT.exe*), GWHAT will need to be redirected to the new location
of the project by repeating the procedure described in the paragraph above.

.. |folder| image:: img/icon_folder.*
                      :width: 1em
                      :height: 1em
                      :alt: folder

.. |new_project| image:: img/icon_new_project.*
                      :width: 1em
                      :height: 1em
                      :alt: stop