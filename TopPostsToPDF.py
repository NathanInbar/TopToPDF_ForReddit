import requests, praw, os, sys, math, time, threading
from io import BytesIO
from PIL import Image
from reportlab.platypus.flowables import Image as RPImage
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from shutil import rmtree
from redditAuthentication import id,secret,agent,name,pswrd


#global variables - - - - -
imageURLS = {}#imageURL dictionary that is filled by the preformScrape() function
imagePermaURL={}#permaURL dictionary (url to the post itself)
postTitles={}#titles of the posts
cwd = os.getcwd()#main directory
saveImgDir=''#directory for where to save images, temp or not
postLimit = -1#set postLimit, sr, and imgDeleteBool to values that would cause an error. there should never be an instance that we use these values without first changing them through takeInputs()
sr='err'
imgDeleteBool='err'
allowedEXT={#dictionary of allowed extension. if files scraped do not have one of these extensions, it will be ignored.
    1:'.png',
    2:'.jpg',
}
# - - - - - - - - - - - -
def takeInputs():
    global postLimit #tell takeInputs we are going to use these global vars, so when we call them it knows to change the global var instead of creating a local var with the same name
    global sr
    global imgDeleteBool
    while True:#create an infinite loop that will run until user gives a valid input
        postLimit = input("Enter amount of posts to scrape (1-1000): ")#take input for amount of Posts to Scrape. Max 1000.
        try:
            postLimit = int(postLimit)
        except ValueError:#ValueError is thrown when postLimit is not a valid int
            print('Invalid Number. Must be an integer')#require an int
            continue
        if 0 <= postLimit <= 1000:#must be 1 to 1000
            break
        else:
            print ('Invalid Range. Must be 1-1000. ')#require int to be 1 to 1000

    sr = input("Enter subreddit name. reddit.com/r/") #take input for subreddit to scrape from. reddit.com/r/...
    imgDeleteBool = input('Delete raw images after compile? (Y or N): ')#boolean to decide whether to delete the image folder or not

    if imgDeleteBool.casefold() == 'n':#change from input string to a boolean. default to deleting images if invalid input is given
        imgDeleteBool = False
    elif imgDeleteBool.casefold() == 'y':
        imgDeleteBool = True
    else:
        print('invalid. Defaulting to Y . . .')
        imgDeleteBool = True
        print(imgDeleteBool)

def createTempFolder():
    global saveImgDir
#create a folder to store the images that will be temporarily written to disk, then deleted once images are put into PDF.  This func is only used if user decides to delete the raw images
    tempFolder = r'{}\Temporary'.format(cwd)
    if not os.path.exists(tempFolder):
        os.makedirs(tempFolder)
    saveImgDir = tempFolder
    print('successfully created Temporary folder . . .')

def createImageFolder():
    global saveImgDir
#create a folder called SavedImages, then another within that which is the subreddits name. This func is only used if user decides to NOT delete the raw images

    siFolder = r'{}\SavedImages'.format(cwd)#saved images folder dir
    srFolder = r'{}\{}'.format(siFolder,sr)#subreddit folder dir
    if not os.path.exists(siFolder):
        os.makedirs(siFolder)
    print('successfully created \'SavedImages\' folder . . .')
    if not os.path.exists(srFolder):
        os.makedirs(srFolder)
    print('successfully created \'{}\' folder in \'SavedImages\' . . .'.format(sr))
    saveImgDir = srFolder

def createPDFfolder():
#create a folder to store the completed PDFs
    pdfFolder = r'{}\PDFs'.format(cwd)
    if not os.path.exists(pdfFolder):
        os.makedirs(pdfFolder)
    print('successfully created PDF folder . . .')

#Authentication to access reddit. Replace id,secret,agent,name,pwrd with your Authentication information in redditAuthentication.py
reddit = praw.Reddit(client_id=id, \
                     client_secret=secret, \
                     user_agent=agent, \
                     username=name, \
                     password=pswrd)
# - - - - - - - - - - - -


def preformScrape(): #this function scrapes a subreddit and compiles image URLs from the top posts into the 'imageURL' dictionary

    subreddit = reddit.subreddit(sr)#target specific subreddit
    posts = subreddit.top(limit=postLimit)#get top posts of all time from targeted subreddit- with amount of posts as 'postLimit'

    index = 0
    def addURL(url):#arg = image url. adds URL to image url dictionary, adds post title & permalink to corresponding dictionaries
        imageURLS[index] = url
        postTitles[index] = post.title
        imagePermaURL[index] = 'http://reddit.com'+post.permalink #http:// is required to hyperlink outside of the PDF

    for post in posts:#iterates through all posts that were scraped
        url = (post.url)

        for ext in allowedEXT: #check image extension with allowed extensions dictionary
            if('{}'.format(allowedEXT.get(ext)) in url): #if image url contains extension type that is in the allowedEXT dict. , then execute the addURL function for that post
                index+=1
                addURL(url)

        print('\rScraping posts: [{}/{}]   '.format(index , postLimit),end='')#console fluff to show scraping progress. \r = carriage return (moves console cursor to beginning of the same line to overwrite)

    print('\nsuccessfully scraped {}/{} posts from r/{} . . .'.format(index, postLimit,sr))#console fluff to show scrape has completed \n = newline


def convertImgs(): # this function will replace all the image URLs in the 'imageURLS' dict with PIL (Python Image Library) image data rather than the URL itself. Also, modifies the image with the specifications below.
    done = False #done controls the spin_cursor function
    def spin_cursor():
        while True:#cool ascii spinners: |/-\\ , .oO@*
            for cursor in '|/-\\': #iterate through this string
                sys.stdout.write(cursor) #write the spinning wheel into console at current cursor position
                sys.stdout.flush() # flush will push the spinning wheel into console in its current state. without this it would wait for the last iteration and then print a single symbol, rather than update to display each symbol in succession.
                time.sleep(0.2) # adjust this to change the speed of the wheel.
                sys.stdout.write('\b')#produces a backspace
                if done:#ends this while loop (does NOT end the thread itself)
                    return

    spin_thread = threading.Thread(target=spin_cursor)#create new spin thread that will run the spin_cursor method when started

    #the convert function is only used inside the convertImgs function. to avoid confusion read the for loop under this function first.
    def convert(img_url):#converts original image to have 24bit depth, RGB image mode, and a width of 300px, height is resized according to aspect ratio. And turn image into a JPEG
        response = requests.get(img_url)#retrieve URL content
        img = Image.open(BytesIO(response.content))#set img to image file from URL's content
        img = img.convert("RGB", palette=Image.ADAPTIVE, colors=24) #converts image to 24bit depth & RGB color mode. Images must be written in the RGB mode. Changing bit depth to 24 reduces computation time significantly
        #changing bit depth means delegating each pixels data to: 8 bits to red, 8 bits to green, and 8 bits to blue. 8*3=24, hence 24bit depth.
        basewidth = 300 #define the width this image will be resized to
        wpercent = (basewidth / float(img.size[0])) #calculate width to height percentage(aspect ratio)
        hsize = int((float(img.size[1]) * float(wpercent))) #calculate what the height for this image must be if width is (basewidth), while preserving aspect ratio. Prevents stretching.
        img = img.resize((basewidth, hsize), Image.ANTIALIAS)#resize image to 'basewidth'px wide by 'hsize'px high- and use Antialiasing
        return img#return the modified image as a 'PIL Image'. PIL Image data is necessary for compatability reasons. This way all images, no matter where they come from, will have equally formatted data. (equality, bitch)

    for img in imageURLS: #iterate through all image URLS
        imageURLS[img] = convert(imageURLS.get(img)) #take the URL and pass it into the "convert" method. then replace the URL with the returned image as a 'PIL Image' object rather than the URL as a string
        imageURLS.get(img).save(r'{}\{}.jpeg'.format(saveImgDir,img), format='JPEG')#get this new value (PIL Image data) and save it as a JPEG image to disk


        if not spin_thread.isAlive():#if the spin_thread has already been started, then DO NOT start it again. Trying to start a thread more than once throws an exception!
            spin_thread.start()#start the thread. (begins running the spin_cursor method)

        completionPercent =  math.trunc((img/len(imageURLS))*100)#calculate how far the conversion process is
        print('\rSaving images: {}%  '.format(completionPercent),end='')#console fluff to display completion percentage

    done = True #stops the spinner thread after all images are converted. (*sad cowboy noises*)
    spin_thread.join()#joins the dead spin_thread to the main thread so we now operate on only 1 thread again.
    print('\nsuccessfully converted {} images to have 24bit depth, RGB color mode, and JPEG extension . . .'.format(len(imageURLS)))#console fluff to display that the conversion was a success
    time.sleep(1)#sleeps for 1 second to add dramatic effect. (heckerman)

def PILtoPDF(): #this function pieces all the data (newly converted images, post titles, and hyperlinks) together into a PDF file
#create a new PDF document with the SimpleDocTemplate from the reportlab.platypus library.The name of the PDF will be the name of the chosen subreddit
    doc = SimpleDocTemplate(r"{}\PDFs\{}.pdf".format(cwd,sr),pagesize=letter,rightMargin=72,leftMargin=72,topMargin=72,bottomMargin=18)

    styles=getSampleStyleSheet()#retrieve a list of text styles that can be used (ex: 'Normal' = Times Roman, size 12)

    Story=[]#create new 'Story' list. This will contain all Flowable elements that will be added to the final document

    for ims in imageURLS:#iterate for however many images we have
    #creates a new 'Flowable' (reportlab.platypus object). The flowable in this instance is a Paragraph. This will contain the post title and be hyperlinked to the post on reddit itself
    #Flowables are what can be appended to Story
        linkedText = Paragraph('<link href="' + '{}'.format(imagePermaURL.get(ims)) + '">' + '{}'.format(postTitles.get(ims)) + '</link>', styles['Heading1'])

        img = imageURLS.get(ims)#retrieve the currently targeted image
        width,height=img.size #determine it's size
        if height > 600:#if the height is 601+px then we want to manually squish the height down to 600px. If you try to insert an image that would extend off a PDF page it will crash.
            img.resize((300,600),Image.ANTIALIAS)#this commences the squishing, and uses Antialiasing. The only other option i saw was to delete it. but whatever. squish is fine.
            height=600#sets height var to 600 so that the height is updated to represent its real value

#this is where PDF elements are shoved into Story's tiny hole.
        Story.append(linkedText)#put the post's hyperlinked title in first
        Story.append(Spacer(1, 12)) #add some white space below it (why isnt there a 'black' space? hmm)
#prepare to be bored:
#in order to insert the image with PIL image data, it has to be cast with reportlab's Image class (RPImage). It seems repetitive because reportlab's Image class stems from PIL but there are differences
#and thus both are necessary. PIL's Image class was used in convertImgs(), Reportlabs Image class is used exclusivly to create the Flowable (oh yeah mr. krabs) which is needed to append to Story.
#After casting, append the image into the Story list with it's size specifications.
        Story.append(RPImage(r"{}\{}.jpeg".format(saveImgDir,ims), width=300,height=height))
        Story.append(PageBreak())#holds the page's family hostage and breaks his poor soul

    doc.build(Story)#take all the elements and waffle stomps them into the PDF document

    pdfSize = os.path.getsize(r"{}\PDFs\{}.pdf".format(cwd,sr))#gets size of the PDF. wont be exact but who cares its fluff

    print('successfully wrote {} images to PDF, along with their hyperlinked titles . . .'.format(len(imageURLS)))#prints a weird flex
    print('PDF size: ~{}kb'.format(math.trunc(pdfSize/1000)))#why did i do this? no one cares about how big the pdf is. oh well
    time.sleep(1)#more dramatic effects

def eraseTrail():#erases image files after they are all put inside the PDF.

    rmtree('Temporary')#recursively deletes all contents of Temporary folder (all the hentai). Then makes the folder disappear faster than my dad at the gas station 16 years ago
    print('successfully removed Temporary folder . . .')

def executeOrder66():#executes all the previously documented functions in the order they should happen. Also, Star Wars.
    takeInputs()
    if imgDeleteBool is True:
        createTempFolder()#create folder to store pictures in
    else:
        createImageFolder()

    preformScrape()#scrape images, form lists
    convertImgs()#convert list from url list to PIL Image data list
    createPDFfolder()#create folder for completd PDFs
    PILtoPDF()#put all imgs/titles in a PDF

    if imgDeleteBool is True:
        eraseTrail()#erase the furry porn downloaded in the process and encrypts all your files. runs ransomware.exe

    postFailures = postLimit - len(imageURLS)#calculates how many posts had an invalid URL or a URL that didn't have an extension at all.

    print('- - - - - - - - - - - - - - - - - -')#prints braille for the blind
    print('Operation Success.')#prints Success mesage in console
    time.sleep(1)#i'm in.
    print('{} out of {} posts were compiled into the PDF successfully.\n{} posts contained an invalid / forbidden file extension, or contained an invalid URL (no extension).'.format(len(imageURLS),postLimit,postFailures))#prints post successes and failures. at least they didn't fail my parents
    time.sleep(1)#is god dead? Was there ever a god in the first place?
    os.system('pause')# suspends Console so it doesn't close after this script is finished. How else would people read the fluff :(

#just to clarify: epstein, in fact, did not kill himself.

# - end of script. Its not 100% optimized but whatever
