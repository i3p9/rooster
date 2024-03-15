# Standardized Rooster Teeth Site Download Tutorial 
####  (edited from tubeup tutorial by Snakepeeker)

The intention of this document is to make it very easy for those with little or no experience using scripts or PowerShell to understand and use Rooster for pulling videos from roosterteeth.com in a standardized fashion as decided by folks of the Archive of Pimps Discord server.

NOTE: It is a good idea (and sometimes necessary) to close and reopen PowerShell after installing items.

Any text in code blocks `like this` are meant to be input into the PowerShell terminal.

## Installing Python

 1. Run PowerShell as Administrator, by pressing <kbd>Windows</kbd> + <kbd>X</kbd>, and choosing *"Powershell (Adminstrator)"*.  It might also be labeled *"Terminal (Administrator)"*.


2. Install Chocolatey following these 5 steps: https://chocolatey.org/install
	- Step 2 is important in particular

3. Restart Powershell and reopen as Admin 
	
4. Install Python by typing this line into PowerShell:
 `choco install python`
 For more help, check here: https://docs.python-guide.org/starting/install3/win/#install3-windows

## Installing PIP & Git

 1. Make sure pip is installed:
  `py -m pip install -U pip`

2. Restart Powershell and reopen as Admin

3. Then install setuptools 
 `pip install setuptools`

4. Restart Powershell and reopen as Admin

5. Install Git via Chocolatey (source: https://community.chocolatey.org/packages/git.install#install)
 `choco install git.install`

6. Restart Powershell and reopen as Admin
## Installing ffmpeg
This is not in PowerShell, open your browser and open the link below. Then click the appropriate button for Windows, Linux or Mac. 
> If you don't know which one you want, you probably want Windows x64

Download an archive with ffmpeg, ffplay and ffprobe from here: https://github.com/yt-dlp/FFmpeg-Builds#ffmpeg-static-auto-builds
 * Unzip the folder and copy all three .exe from bin folder
 * Paste the three .exe files in C:\Python312\Scripts
 
 ## Installing the "rooster" script made by @fhm

How to install Rooster (edited from [this Discord post](https://discord.com/channels/1215032770695401592/1216838057299546154/1217171363580739614%29))

1. Restart PowerShell and reopen as Admin
2. Within Powershell type either
`pip3 install git+https://github.com/i3p9/rooster.git`
-OR-
`pip install git+https://github.com/i3p9/rooster.git`


3. If you already have it installed you may use either of the following commands to upgrade the current installation:
 `pip3 install git+https://github.com/i3p9/rooster.git -U`
-OR- 
 `pip install git+https://github.com/i3p9/rooster.git -U`

## Using "rooster" script

 1. Open a folder
 2. Hold shift and right click, in the context menu, and select "open PowerShell here"  
 

> alternatively. open PowerShell and
    use the "cd" command to change directory:
     `cd
    C:Users\Username\Videos\RoosterTeeth`

3. Optional - create a textfile "filelist.txt" (the name does not matter) to dump links into for the script to reference. When you see "filelist.txt" in the command this is the file its referencing.

4. Once in PowerShell, run the script using this line, changing your email and password as necessary (keep the quotation marks)
`rooster --email "your@email.com" --password "your-password" --show url or filelist.txt`

5. It will download the files in a new folder, from where you ran it from along with all necessary data.

6. You can either put a url: https://roosterteeth.com/watch/xxx(has to be episode url, not season url)
Or a list of links, e.g. funhaus_first.txt which contains a list of all funhaus first episodes.
**For this project, we are assigning groups of videos by text file, so use those.**

Examples:

 ❗❗❗ ***This should be the command you use if you're helping with the archive project:*** ❗❗❗
` rooster --email "caboose@RVB.com" --password "sargesucks2" --show rwby_links.txt`

This example is only for archiving individual videos or shows.  You can use it, but for archiving with us please use the above line.
` rooster --email "caboose@RVB.com" --password "sargesucks22" --show https://roosterteeth.com/watch/so-alright-2024-sa29`

## Advanced Options
#### Don't use these unless you know what you're doing!
Other parameters:
> `--show`:  Assumes show mode, which will download the episode to their respective Show folder inside Downloads
limitations: if we fall back to data parser 3, it will not work and use the default directory mode.

> the filelist.txt should be in the directory that PowerShell is working in. (type `pwd` if you're not sure where you are)

> `--concurrent-fragments`: NUMBER , default is 10 if you don't put anything. Should be good enough.




