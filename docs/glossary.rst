Glossary
=================================

.. glossary::
   :sorted:

   Project folder
       Folder where are stored all input and output files relative to a particular
       project.
       
   Raw folder
       Folder where are saved the daily weather data files once they have been
       downloaded from the CDCD as described in :numref:`sec_download_weather_data`.
       
   Input folder      
       Folder where are saved by default the formatted weather data files generated
       from downloaded raw data files. 
       This folder is also the default location where the tool to fill the gaps in 
       daily weather data records look for input data files as described in
       :numref:`sec_loading_weather_data`.

   Excel numeric date format
       Excel stores dates as sequential serial numbers, representing the
       number of days, in decimal format, since January 1, 1900. For example,
       January 1, 2008 6:00 AM is serial number 39448.25 because it is 
       39,447 days and 1/4 after January 1, 1900. Dates before January 1, 1900
       is thus not supported by this format.
       