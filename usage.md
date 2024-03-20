
## Usage
Input: Accepts 3 kinds of inputs

* `link.txt` -> A collection of Roosterteeth Episode links, seperated by new line.
* Series Link -> Processes an entire series 
*  Season Link -> Processes an entire season of a series

### Mandatory
* `--email` and `--password` | while RT supports downloading without Login but a logged in session is less likely to be throttled or rejected
* Usage Type (Use either one of them):
	* `--ia` : Uploads to Internet Archive with proper metadata. Requires you to run `ia configure` once to setup your Internet Archive Account
	 * `--show`: Primarily used for downloading. Uses a opinionated folder and file structure. 
  
### Recommended
* `--fast-check`: Checks for duplicate downloads in a much faster way, runs locally. Note: You need to run the script in the same location to have `--fast-check` work.

### Optional
* `--random`: Randomizes 
* `--skip-corrupt-fragments`: Default: True 
	* Abort and skip to the next download if any of the fragments are corrupted during download
	* It's advisable not to use this, you can use it if you want to salvage a incomplete video file.
* `--fragment-retries` Default: 10
	* How many times to retry if a individual fragment download fails. Default is set to 10. It's good enough but if you are downloading from a network/host with spotty network it wouldn't hurt to increase it. 
* `--concurrent-fragments`: Default: 10
	* How many concurrent fragments to download a file with. If you are facing slower download speeds you could increase the default value and see if anything changes.

### Upload to IA Specific
* `--keep-uploads`: If you add this, it will keep the successfully uploaded to IA files. 
* `--i`: By default a upload will be skipped if same itemname already exists. But if for some reason you missed a file or upload failed for some reason, you can do the command it and will ignore existing upload.
	* Note: It still checks for duplicates on a file by file basis, only uploads the missing files.
* `--update-meta`: Only updates the metadata, no file transfers. Only use it for messed up uploads.

### Misc.
* `--use-aria`: Uses aria2c as a downloader if you have it installed

### Examples
Downloads form a list of links and uploads to IA. Deletes the files after successful uploads.

    #uploading from a list of links
    rooster --email "yourname@gmail.com" --password "pass" --ia --fast-check 'links.txt'
    # downloading a full series
    rooster --email "yourname@gmail.com" --password "pass" --ia --fast-check https://roosterteeth.com/series/gameplay
