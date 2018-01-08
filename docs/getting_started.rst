Getting Started
==========================================================

.. _sec_installing_on_windows:

Installing GWHAT on a Windows system
----------------------------------------------------------

First of all, the latest binary distribution of GWHAT, packaged as a zip archive,
must be downloaded from the project Releases_ [#url_r]_ page on GitHub.
Then the content of the zip archive needs to be extracted in a directory with
:file:`Write` [#write]_ permission. This will result in a directory containing
a folder named :file:`GWHAT`, which contains several files including a file
named :program:`gwhat.exe`.
GWHAT can then be started simply by double clicking on this file, no
installation is required.

The installation directory will also contain a folder named :file:`Projects`,
where all input and output files used and created by GWHAT are stored by default.
This folder includes a project example with samples of input and output files
to test and learn the various features of the program.

.. note:: Please help GWHAT by reporting bugs or proposing new features
          in our `Issues Tracker`_ [#url_it]_ on GitHub.


Updating GWHAT on a Windows system
----------------------------------------------------------

It is possible to check if updates are available for GWHAT by clicking on the
button :guilabel:`Check for Updates` in the :guilabel:`About GWHAT` window,
which can be accessed by clicking on the |icon_info| icon as shown in
:numref:`scs_gwhat_check_updates`.

.. _scs_gwhat_check_updates:
.. figure:: img/scs/updates_window.*
    :align: center
    :width: 100%
    :alt: alternate text
    :figclass: align-center

    Presentation of the tool to check if updates are available for GWHAT.

To update GWHAT to a newer version, the latest binary distribution of the
software, packaged as a zip archive, needs first to be downloaded from
the project Releases_ page on GitHub.
Then, in the directory where GWHAT was installed, the folder named :file:`GWHAT`
needs to be replaced manually with the one that is included in the zip archive
that was just downloaded. The new version of GWHAT can then be started simply
by clicking on the :program:`gwhat.exe`, located in the new :file:`GWHAT` folder.


Running GWHAT from the source files
----------------------------------------------------------

Binary distribution are currently produced only for Windows systems.
However, GWHAT can run on Windows, Linux, or macOS computer operating systems
directly from the source files.


.. _Releases: https://github.com/jnsebgosselin/gwhat/releases/latest
.. _Issues Tracker: https://github.com/jnsebgosselin/gwhat/issues

.. |icon_info| image:: img/icon/icon_info.*
                      :width: 1em
                      :height: 1em
                      :alt: stop

.. rubric:: Footnotes
.. [#url_r] https://github.com/jnsebgosselin/gwhat/releases/latest
.. [#write] Permits adding of files and subfolders (https://msdn.microsoft.com/en-us/library/bb727008.aspx).
.. [#url_it] https://github.com/jnsebgosselin/gwhat/issues
