
# Standardized Rooster Teeth Site Download Tutorial 
####  (edited from tubeup tutorial by Snakepeeker)

[Archive of Pimps Discord](https://discord.gg/SHCURNvG8v)

The intention of this document is to make it very easy for those with little or no experience using scripts or PowerShell to understand and use Rooster for downloading videos from roosterteeth.com in a *standardized fashion* as decided by folks of the Archive of Pimps Discord server.

> NOTE: It is a good idea (and sometimes necessary) to close and reopen PowerShell after installing items.

Any text in code blocks `like this` are meant to be input into the PowerShell terminal.

## Installing Python

 1. Run PowerShell as Administrator, by pressing <kbd>Windows</kbd> + <kbd>X</kbd>, and choosing *"Powershell (Adminstrator)"*.  It might also be labeled *"Terminal (Administrator)"*.


2. Install Chocolatey: (adapted from https://chocolatey.org/install)
    1. First, ensure that you are using Powershell (Administrator) as discussed in the previous step.
    2. ```Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))```
Paste the copied text into your shell and press Enter.
Wait a few seconds for the command to complete.
If you don't see any errors, you are ready to use Chocolatey! Type choco or choco -? now, or see Getting Started for usage instructions.
	



3. Restart Powershell and reopen as Admin 
	
4. Install Python by typing this line into PowerShell:
 `choco install python`
 For more help, check here: https://docs.python-guide.org/starting/install3/win/#install3-windows

## Installing PIP & Git

 1. Make sure pip is installed:
  `py -m pip install -U pip`

2. Then install setuptools 
 `pip install setuptools`

3. Restart Powershell and reopen as Admin

4. Install Git via Chocolatey (source: https://community.chocolatey.org/packages/git.install#install)
 `choco install git.install`

5. Restart Powershell and reopen as Admin
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

> [The Discord](https://discord.gg/SHCURNvG8v) has lists of links to work on.

4. Once in PowerShell, run the script using this line, changing your email and password as necessary (keep the quotation marks)
`rooster --email "your@email.com" --password "your-password" --show url or filelist.txt`

5. It will download the files in a new folder, from where you ran it from along with all necessary data.

6. You can either put a url: https://roosterteeth.com/watch/xxx (must be episode url, not season url)
Or a list of links, e.g. funhaus_first.txt which contains a list of all funhaus first episodes.
**For this project, we are assigning groups of videos by text file, so use those.**

Examples:

 ❗❗❗ ***This should be the command you use if you're helping with the archive project:*** ❗❗❗
` rooster --email "caboose@RVB.com" --password "sargesucks2" --show rwby_links.txt`

This example is only for archiving individual videos or shows.  You can use it, but for archiving with us please use the above line.
` rooster --email "caboose@RVB.com" --password "sargesucks2" --show https://roosterteeth.com/watch/so-alright-2024-sa29`

If using a list of files, (e.g. `filelist.txt`) it must be in your [current working directory](https://www.computerhope.com/jargon/c/currentd.htm). (type `pwd` if you're not sure where you are)

### Arguments for downloading Rooster Teeth content locally
 `--show`:  Assumes show mode, which will download the episode to their respective show folder.
 > ❗❗❗`--show` is required if you want to contribute your downloads to the Archive of Pimps project. ❗❗❗
 
 `--concurrent-fragments XX`: Where `XX` is a number, this determines how many concurrent fragments you will download at a time from Rooster Teeth's website.  Default is 10.
 
 `--fast-check`: Checks if the program has already downloaded and uploaded a video to archive.org, and if so, skips it.

 
### Arguments for uploading Rooster Teeth site content to archive.org 
 `--ia`: triggers uploading to archive.org.  By default, this also deletes the download on the local system after uploading.

`--concurrent-fragments XX`: Where `XX` is a number, this determines how many concurrent fragments you will download at a time from Rooster Teeth's website.  Default is 10.
 `--fast-check`: Unknown
 `--keep-uploads`: retains a local copy of uploaded content.
 > NOTE: `--keep-uploads` uses a different file structure than the local downloader (`--show`), so it is not suitable for local backup. Its ideal usecase is if your archive.org uploads fail often.


`--i`: Ignore existing uploaded items. Works in the same way as [tubeup](https://github.com/bibanon/tubeup)'s `--ignore-existing-item` — if a file is missing on a upload, you can re-run the problem link with `-i` to fill in the gaps. Only works with uploads on **YOUR** account.
> NOTE: only use this if your archive.org uploads have failed, or are missing files. **Never use when running the script for the first time.**

### Advanced/Other Options
#### ***Don't use these unless you know what you're doing!***
Other parameters:
 
 `--update-meta`: Optional: If you notice problems with your METADATA ***on archive.org only***, then run this. **DO NOT** bulk update your archives, only use this flag for problem links.
 
 `--use-aria`: uses [aria2](https://aria2.github.io/) to download using an alternate fragmenting utility. From our testing, this does not result in faster speeds than default - in fact, it is usually slower.

`--fragment-retries XX`: Where `XX` is a number, this determines how many times each video fragment will retry downloading after failing. If your connection is spotty or your downloads keep failing, adding this argument might help.
`--skip-corrupt-fragments`: Setting that allows the program to continue if rooster fails to download all fragments of a video. By default, rooster *will* stop if it cannot download a fragment correctly.

---
`README.md` written by @schmintendo and @c3someran, based on @snakepeeker's initial tutorial
<kbd>♡RT♡</kbd> 

