# Import modules
import discord
import os
import wikipedia
from random import randint
from discord.ext import commands
from google_images_download import google_images_download
import requests
import shutil
import eyed3

# Initialize library
response = google_images_download.googleimagesdownload() 

# Initialize bot
bot = commands.Bot(command_prefix=['b!','b.','b#'], case_insensitive = True, description="BirdID - Your Very Own Ornithologist")

# Valid file types
valid_extensions = ["jpg", "png", "jpeg"]

#achievement values
achievement = [10, 25, 50, 100, 150, 200, 250, 400, 420, 500, 650, 690]

# Setup Variables
currentBird = ""
answered = True
currentSongBird = ""
songAnswered = True
totalCorrect = 0
prevJ = 20 #make sure it sends a diff image
prevB = "" #make sure it sends a diff bird
prevS = "" #make sure it sends a diff song
dictOfServers = {
  # "ctx.channel.id" : ["bird","answered","songbird","songanswered", "totalCorrect", "goatsucker", "goatsucker answered"]
}
userCount = {
  #user:[username, #ofcorrect]
}

# Converts txt file of birds into list
birdList = []
with open('birdList.txt','r') as fileIn:
  for line in fileIn:
    birdList.append(line.strip('\n'))
print("birdList done!")

# Converts txt file of scientific birds into list
sciBirdList = []
with open('scibirds.txt','r') as fileIn:
  for line in fileIn:
    sciBirdList.append(line.strip('\n'))
print("sciBirdList done!")

#converts meme txt into list
memeList = []
with open('memes.txt','r') as fileIn:
  for line in fileIn:
    memeList.append(line.strip('\n'))
  print("memeList done!")

# Converts txt file of songbirds into list
songBirds = []
with open('birdsongs.txt','r') as fileIn:
  for line in fileIn:
    songBirds.append(line.strip('\n'))
  print("songBirds done!")

# Converts txt file of scientific songbirds into list
sciSongBirds = []
with open('scibirdsongs.txt','r') as fileIn:
  for line in fileIn:
    sciSongBirds.append(line.strip('\n'))
  print("sciSongBirds done!")

# Logging
@bot.event
async def on_ready():
  print("Logged in as:")
  print(bot.user.name)
  print(bot.user.id)
  print("_" * 50)
  await bot.change_presence(activity=discord.Activity(type=3, name="birds")) # Change discord activity

######
# FUNCTIONS
######

# Function to run on error
def error_skip(ctx):
  dictOfServers[ctx.channel.id][1] = True
  dictOfServers[ctx.channel.id][0] = ""

# Function to send a bird picture:
# ctx - context for message (discord thing)
# bird - bird picture to send (str)
# message - text message to send before bird picture (str)
# addOn - string to append to search for female/juvenile birds (str)
async def send_bird(ctx, bird, on_error=None, message=None, addOn = ""):
  global prevJ
  global dictOfServers


  if bird == "":
    print("error - bird is blank")
    await ctx.send("There was an error fetching birds. Please try again.")
    dictOfServers[ctx.channel.id][0] = ""
    dictOfServers[ctx.channel.id][1] = False
    if on_error:
      on_error(ctx)
    return

  await ctx.send("**Fetching.** This may take a while.", delete_after=10.0)
  # trigger "typing" discord message
  await ctx.trigger_typing()

  sciBird = bird

  #creating list of arguments
  print("scibird: "+str(sciBird))
  arguments = {"keywords":sciBird + str(addOn),"limit":5,"print_urls":True}   
  #passing the arguments to the function
  paths = response.download(arguments)
  print("paths: "+str(paths))
  paths = paths[0]
  myList = [paths [i] for i in sorted(paths.keys()) ]
  myList = myList[0]
  print("myList: "+str(myList))

  j = randint(0, int((len(myList)-len(myList)%2)/2)) # Randomize start
  while j == prevJ:
    j = randint(0, int((len(myList)-len(myList)%2)/2)) # Randomize start
  prevJ = j
    
  for x in range(j,len(myList)): # check file type and size
    image_link = myList[x]
    extension = image_link.split('.')[len(image_link.split('.'))-1]
    print("extension: "+str(extension))
    statInfo = os.stat(image_link)
    if extension.lower() in valid_extensions and statInfo.st_size < 8000000: # 8mb discord limit
      print("found one!")
      break
    print("size: "+str(statInfo.st_size))

  filename = str(image_link)
  statInfo = os.stat(filename)
  if statInfo.st_size > 8000000: # another filesize check
    await ctx.send("Oops! File too large :(")
  else:
    with open(filename,'rb') as img:
      if message:
        await ctx.send(message)
      await ctx.send(file=discord.File(img, filename="bird."+extension)) # change filename to avoid spoilers

  # clear downloads
  try:
    shutil.rmtree(r'downloads/')
    print("Cleared downloads.")
  except FileNotFoundError:
    print("Already cleared.")

#sends a birdsong
async def send_birdsong(ctx, bird, message = None):
  await ctx.send("**Fetching.** This may take a while.", delete_after=10.0)
  # trigger "typing" discord message
  await ctx.trigger_typing()
  if bird in songBirds:
    index = songBirds.index(bird)
    sciBird = sciSongBirds[index]
  else:
    sciBird = bird
  # fetch sounds
  query = sciBird.replace(" ", "%20")
  response = requests.get("https://www.xeno-canto.org/api/2/recordings?query="+query+"%20q:A&page=1")

  if response.status_code == 200:
    recordings=response.json()["recordings"]
    print("recordings: "+str(recordings))
    if len(recordings) == 0: # bird not found
      # try with common name instead
      query = bird.replace(" ", "%20")
      response = requests.get("https://www.xeno-canto.org/api/2/recordings?query="+query+"%20q:A&page=1")
      if response.status_code == 200:
        recordings=response.json()["recordings"]
      else:
        await ctx.send("**A GET error occurred when fetching the song. Please try again.**")
        print("error:" + str(response.status_code))     

    if len(recordings) != 0:
      url=str("http:"+recordings[randint(0,len(recordings)-1)]["file"])

      songFile = requests.get(url)
      if songFile.status_code == 200:
        with open("birdsong.mp3", 'wb') as fd:
          fd.write(songFile.content)

        # send sounds
        with open("birdsong.mp3",'rb') as song:
          audioFile = eyed3.load("birdsong.mp3")
          audioFile.tag.title = u"Birb noises"
          audioFile.tag.comment = u"Birb noises"
          audioFile.tag.save()
          if message:
            await ctx.send(message)
            await ctx.send(file=discord.File(song, filename="bird.mp3")) # change filename to avoid spoilers
      else:
        await ctx.send("**A GET error occurred when fetching the song. Please try again.**")
        print("error:" + str(songFile.status_code))  
    else:
      await ctx.send("Unable to get song - bird was not found.")

  else:
    await ctx.send("**A GET error occurred when fetching the song. Please try again.**")
    print("error:" + str(response.status_code))

# spellcheck - allows one letter off/extra
def spellcheck(worda,wordb):
  wrongcount = 0
  longerword = []
  shorterword = []
  list1 = [char for char in worda]
  list2 = [char for char in wordb]
  if worda!=wordb:
    if len(list1) > len(list2):
      longerword = list1
      shorterword = list2
    elif len(list1)<len(list2):
      longerword = list2
      shorterword = list1
    else:
      for i in range(len(list1)):
        if list1[i] == list2[i]:
          pass
        else:
          wrongcount += 1
      if wrongcount >1:
        return False
      else:
        return True
    if abs(len(longerword)-len(shorterword)) > 1:
      return False
    else:
      for i in range(len(shorterword)):
        try:
          if longerword[i] != shorterword[i]:
            wrongcount += 1
            del longerword[i]
        except:
          return False
      if wrongcount < 2:
        return True
      else:
        return False
  else:
    return True

# Command to set up a set of dict values
async def setup(ctx):
  global dictOfServers
  if ctx.channel.id in dictOfServers:
    return
  else:
    dictOfServers[ctx.channel.id] = ["", True, "", True, 0, "", True]
    await ctx.send("Ok, setup! I'm all ready to use!")

#sets up new user
async def userSetup(ctx):
  global userCount
  if ctx.message.author.id in userCount:
    return
  else:
    userCount[ctx.message.author.id] = [str(ctx.message.author),0]
    await ctx.send("Welcome " + str(ctx.message.author) + "!")

######
# COMMANDS
######

# Bird command - no args
@bot.command(help = '- Sends a random bird image for you to ID', aliases = ["b"], usage="[female|juvenile]") # help text
@commands.cooldown(1, 10.0, type=commands.BucketType.channel) # 10 second cooldown
async def bird(ctx, add_on = ""):
  global dictOfServers

  await setup(ctx)
  await userSetup(ctx)

  if (add_on == "female" or add_on == "juvenile")or add_on == "":
    pass
  else:
    await ctx.send("This command only takes female, juvenile, or nothing!")
    return

  print("bird")
  global answered
  global prevB
  answered = dictOfServers[ctx.channel.id][1]
  # check to see if previous bird was answered
  if answered == True: # if yes, give a new bird
    dictOfServers[ctx.channel.id][1] = False
    currentBird = birdList[randint(0,len(birdList)-1)]
    while currentBird == prevB:
      currentBird = birdList[randint(0,len(birdList)-1)]
    prevB = currentBird
    dictOfServers[ctx.channel.id][0] = currentBird
    print("currentBird: "+str(currentBird))
    await send_bird(ctx, currentBird, error_skip, message="*Here you go!* \n**Use `o>bird` again to get a new picture of the same bird, or `o>skip` to get a new bird. Use `o>check guess` to check your answer. Use `o>hint` for a hint.**", addOn = add_on)
  else: #if no, give the same bird
    await send_bird(ctx, dictOfServers[ctx.channel.id][0], error_skip, message="*Here you go!* \n**Use `o>bird` again to get a new picture of the same bird, or `o>skip` to get a new bird. Use `o>check guess` to check your answer.**", addOn = add_on)
    dictOfServers[ctx.channel.id][1] = False

# goatsucker command - no args
@bot.command(help = '- Sends a random goatsucker to ID', aliases = ["gs"]) # help text
@commands.cooldown(1, 5.0, type=commands.BucketType.channel) # 5 second cooldown
async def goatsucker(ctx):
  global dictOfServers

  await setup(ctx)
  await userSetup(ctx)
  
  print("goatsucker")
  goatsuckers = ["Common Pauraque","Chuck-will's-widow","Whip-poor-will"]
  answered = dictOfServers[ctx.channel.id][6]
  # check to see if previous bird was answered
  if answered == True: # if yes, give a new bird
    dictOfServers[ctx.channel.id][6] = False
    currentBird = goatsuckers[randint(0,2)]
    dictOfServers[ctx.channel.id][5] = currentBird
    print("currentBird: "+str(currentBird))
    await send_bird(ctx, currentBird, message="*Here you go!* \n**Use `o>bird` again to get a new picture of the same goatsucker, or `o>skipgoat` to get a new bird. Use `o>checkgoat guess` to check your answer. Use `o>hint` for a hint.**")
  else: #if no, give the same bird
    await send_bird(ctx, dictOfServers[ctx.channel.id][5], message="*Here you go!* \n**Use `o>bird` again to get a new picture of the same bird, or `o>skip` to get a new bird. Use `o>check guess` to check your answer.**")
    dictOfServers[ctx.channel.id][6] = False

#picks a random bird call to send
@bot.command(help = "- Sends a bird call to ID")
@commands.cooldown(1, 10.0, type=commands.BucketType.channel)
async def song(ctx):
  global dictOfServers
  await setup(ctx)
  await userSetup(ctx)

  global songAnswered
  print("song")
  songAnswered = dictOfServers[ctx.channel.id][3]
  # check to see if previous bird was answered
  if songAnswered == True: # if yes, give a new bird
    global currentSongBird
    v = randint(0,len(songBirds)-1)
    currentSongBird = songBirds[v]
    while currentSongBird == prevS:
      currentSongBird = songBirds[randint(0,len(songBirds)-1)]
    dictOfServers[ctx.channel.id][2] = currentSongBird
    print("currentSongBird: "+str(currentSongBird))
    await send_birdsong(ctx, currentSongBird, message="*Here you go!* \n**Use `o>song` again to get a new sound of the same bird, or `o>skipsong` to get a new bird. Use `o>checksong guess` to check your answer. Use `o>hintsong` for a hint.**")
    dictOfServers[ctx.channel.id][3] = False
  else:
    await send_birdsong(ctx, dictOfServers[ctx.channel.id][2], message="*Here you go!* \n**Use `o>song` again to get a new sound of the same bird, or `o>skipsong` to get a new bird. Use `o>checksong guess` to check your answer. Use `o>hintsong` for a hint.**")
    dictOfServers[ctx.channel.id][3] = False

# Check command - argument is the guess
@bot.command(help='- Checks your answer.', usage="guess", aliases=["guess","c"])
@commands.cooldown(1, 5.0, type=commands.BucketType.channel) # 3 second cooldown
async def check(ctx, *, arg):
  print("check")
  global dictOfServers
  global userCount
  global achievement

  await setup(ctx)
  await userSetup(ctx)

  totalCorrect = dictOfServers[ctx.channel.id][4]
  currentBird = dictOfServers[ctx.channel.id][0]
  if currentBird == "": # no bird
    await ctx.send("You must ask for a bird first!")
  else: #if there is a bird, it checks answer
    index = birdList.index(currentBird)
    sciBird = sciBirdList[index]
    dictOfServers[ctx.channel.id][1] = True
    dictOfServers[ctx.channel.id][0] = ""
    if spellcheck(arg.lower().replace("-"," "),currentBird.lower().replace("-"," "))== True:
      await ctx.send("Correct! Good job!")
      page = wikipedia.page(sciBird)
      await ctx.send(page.url)
      dictOfServers[ctx.channel.id][4] += 1
      userCount[ctx.message.author.id][1] += 1
      if userCount[ctx.message.author.id][1]in achievement:
        number = str(userCount[ctx.message.author.id][1])
        await ctx.send("Wow! You have answered "+number+" birds correctly!")
        filename = 'achievements/'+ number +".PNG"
        with open(filename,'rb') as img:
          await ctx.send(file=discord.File(img, filename="award.png"))

    else:
      await ctx.send("Sorry, the bird was actually " + currentBird.lower() + ".")
      page = wikipedia.page(sciBird)
      await ctx.send(page.url)
    print("currentBird: "+str(currentBird.lower().replace("-"," ")))
    print("args: "+str(arg.lower().replace("-"," ")))
    #send wikipedia page

# Check command - argument is the guess
@bot.command(help='- Checks your goatsucker.', usage="guess", aliases=["cg"])
@commands.cooldown(1, 5.0, type=commands.BucketType.channel) # 3 second cooldown
async def checkgoat(ctx, *, arg):
  print("checkgoat")
  global dictOfServers
  global userCount
  global achievement

  await setup(ctx)
  await userSetup(ctx)

  totalCorrect = dictOfServers[ctx.channel.id][4]
  currentBird = dictOfServers[ctx.channel.id][5]
  if currentBird == "": # no bird
    await ctx.send("You must ask for a bird first!")
  else: #if there is a bird, it checks answer
    index = birdList.index(currentBird)
    sciBird = sciBirdList[index]
    dictOfServers[ctx.channel.id][6] = True
    dictOfServers[ctx.channel.id][5] = ""
    if spellcheck(arg.lower().replace("-"," "),currentBird.lower().replace("-"," "))== True:
      await ctx.send("Correct! Good job!")
      page = wikipedia.page(sciBird)
      await ctx.send(page.url)
      dictOfServers[ctx.channel.id][4] += 1
      userCount[ctx.message.author.id][1] += 1
      if userCount[ctx.message.author.id][1]in achievement:
        number = str(userCount[ctx.message.author.id][1])
        await ctx.send("Wow! You have answered "+number+" birds correctly!")
        filename = '/home/runner/downloads/achievements/'+ number +".PNG"
        with open(filename,'rb') as img:
          await ctx.send(file=discord.File(img, filename="award.png"))

    else:
      await ctx.send("Sorry, the bird was actually " + currentBird.lower() + ".")
      page = wikipedia.page(sciBird)
      await ctx.send(page.url)
    print("currentBird: "+str(currentBird.lower().replace("-"," ")))
    print("args: "+str(arg.lower().replace("-"," ")))
    #send wikipedia page

#checks the song
@bot.command(help = '- Checks the song', aliases=["songcheck","cs","sc"])
@commands.cooldown(1,10.0, type=commands.BucketType.channel)
async def checksong(ctx, *, arg):
  print("checksong")
  global dictOfServers
  await setup(ctx)
  await userSetup(ctx)

  currentSongBird = dictOfServers[ctx.channel.id][2]
  placeholder = currentSongBird
  if currentSongBird == "": # no bird
    await ctx.send("You must ask for a bird call first!")
  else: #if there is a bird, it checks answer
    dictOfServers[ctx.channel.id][2] = ""
    dictOfServers[ctx.channel.id][3] = True
    if spellcheck(arg.lower().replace("-"," "),currentSongBird.lower().replace("-"," "))== True:
      await ctx.send("Correct! Good job!")
    else:
      await ctx.send("Sorry, the bird was actually " + currentSongBird.lower() + ".")
    print("currentSongBird: "+str(currentSongBird.lower().replace("-"," ").strip('(bird)')))
    print("args: "+str(arg.lower().replace("-"," ")))
    dictOfServers[ctx.channel.id][2] = ""
    dictOfServers[ctx.channel.id][3] = True
    #send wikipedia page
    page = wikipedia.page(placeholder+"(bird)")
    await ctx.send(page.url)

# Skip command - no args
@bot.command(help="- Skip the current goatsucker to get a new one", aliases = ["sg"])
@commands.cooldown(1, 5.0, type=commands.BucketType.channel) # 3 second cooldown
async def skipgoat(ctx):
  print("skipgoat")
  global dictOfServers
  await setup(ctx)
  await userSetup(ctx)

  currentBird = dictOfServers[ctx.channel.id][5]
  dictOfServers[ctx.channel.id][6] = True
  dictOfServers[ctx.channel.id][5] = ""
  if currentBird != "": #check if there is bird
    birdPage = wikipedia.page(currentBird+"(bird)")
    await ctx.send("Ok, skipping " + birdPage.url) #sends wiki page
  else:
    await ctx.send("You need to ask for a bird first!")

# Skip command - no args
@bot.command(help="- Skip the current bird to get a new one", aliases = ["s"])
@commands.cooldown(1, 5.0, type=commands.BucketType.channel) # 3 second cooldown
async def skip(ctx):
  print("skip")
  global dictOfServers
  await setup(ctx)
  await userSetup(ctx)

  currentBird = dictOfServers[ctx.channel.id][0]
  dictOfServers[ctx.channel.id][1] = True
  dictOfServers[ctx.channel.id][0] = ""
  if currentBird != "": #check if there is bird
    birdPage = wikipedia.page(currentBird+"(bird)")
    await ctx.send("Ok, skipping " + birdPage.url) #sends wiki page
  else:
    await ctx.send("You need to ask for a bird first!")

# Skip song command - no args
@bot.command(help="- Skip the current bird call to get a new one", aliases=["songskip","ss"])
@commands.cooldown(1, 10.0, type=commands.BucketType.channel) # 3 second cooldown
async def skipsong(ctx):
  print("skip")
  global dictOfServers
  await setup(ctx)
  await userSetup(ctx)

  dictOfServers[ctx.channel.id][3] = True
  currentSongBird = dictOfServers[ctx.channel.id][2]
  if currentSongBird != "": #check if there is bird
    birdPage = wikipedia.page(currentSongBird+"(bird)")
    await ctx.send("Ok, skipping " + birdPage.url) #sends wiki page
  else:
    await ctx.send("You need to ask for a bird first!")

#give hint
@bot.command(help="- Gives first letter of current bird", aliases = ["h"])
@commands.cooldown(1, 3.0, type=commands.BucketType.channel) # 3 second cooldown
async def hint(ctx):
  global dictOfServers
  await setup(ctx)
  await userSetup(ctx)

  currentBird = dictOfServers[ctx.channel.id][0]
  if currentBird != "": #check if there is bird
    await ctx.send("The first letter is " + currentBird[0])
  else:
    await ctx.send("You need to ask for a bird first!")

#give hint for song
@bot.command(help="- Gives first letter of current bird call", aliases = ["songhint","hs","sh"])
@commands.cooldown(1, 3.0, type=commands.BucketType.channel) # 3 second cooldown
async def hintsong(ctx):
  global dictOfServers
  await setup(ctx)
  await userSetup(ctx)

  currentSongBird = dictOfServers[ctx.channel.id][2]
  if currentSongBird != "": #check if there is bird
    await ctx.send("The first letter is " + currentSongBird[0])
  else:
    await ctx.send("You need to ask for a bird first!")

#Gives call+image of 1 bird
@bot.command(help = "- Gives an image and call of a bird", aliases = ['i'])
@commands.cooldown(1, 10.0, type=commands.BucketType.channel)
async def info(ctx, *, arg):
  await userSetup(ctx)

  bird = arg
  print("info")
  await ctx.send("Please wait a moment.")
  await send_bird(ctx, str(bird), message = "Here's the image!")
  await send_birdsong(ctx, str(bird),  "Here's the call!")

# Wiki command - argument is the wiki page
@bot.command(help="- Fetch the wikipedia page for any given argument")
@commands.cooldown(1, 8.0, type=commands.BucketType.channel) # 8 second cooldown
async def wiki(ctx, *, arg):
  print("wiki")
  try:
    page = wikipedia.page(arg)
    await ctx.send(page.url)
  except wikipedia.exceptions.DisambiguationError:
    await ctx.send("Sorry, that page was not found.")
  except wikipedia.exceptions.PageError:
    await ctx.send("Sorry, that page was not found.")

# returns total number of correct answers so far
@bot.command(help = "- total correct answers")
@commands.cooldown(1, 8.0, type=commands.BucketType.channel)
async def score(ctx):
  global dictOfServers
  await setup(ctx)
  await userSetup(ctx)

  totalCorrect = dictOfServers[ctx.channel.id][4]
  await ctx.send("Wow, looks like a total of " + str(totalCorrect) + " birds have been answered correctly in this channel! Good job everyone!")

# meme command - sends a random bird video/gif
@bot.command(help = "- sends a funny bird video!")
@commands.cooldown(1, 300.0, type=commands.BucketType.channel)
async def meme(ctx):
  x=randint(0,len(memeList))
  await ctx.send(memeList[x])

# sends correct answers by a user
@bot.command(help = "- how many correct answers given by a user, mention someone to get their score, don't mention anyone to get your score", aliases = ["us"])
async def userscore(ctx, user=None):
  global userCount
  if user:
    try:
      usera = int(user[1:len(user)-1].strip("@!"))
      print(usera)
    except:
      await ctx.send("Mention a user!")
      return
    print(userCount.keys())
    if usera in userCount.keys():
      times = str(userCount[usera][1])
      user = userCount[usera][0]
    else:
      await ctx.send("This user does not exist on our records!")
      return
  else:
    try:
      user = str(ctx.message.author)
      times = str(userCount[ctx.message.author.id][1])
    except:
      await ctx.send("You haven't used this bot yet! (except for this)")
      return
  await ctx.send(user + " has answered correctly " + times + " times.")

@bot.command(help = "- Top scores, can be between 1 and 5, default is 3", aliases = ["lb"])
async def leaderboard(ctx, placings = 3):
  global userCount
  leaderboard = []
  try: 
    y = (placings+1)
  except:
    await ctx.send("Not an integer.")
  if placings > 5 or placings < 1:
    await ctx.send("Not a valid number. Pick one between 1 and 5!")
  for key, value in userCount.items():
    leaderboard.append([value[1],value[0]])
    leaderboard.sort(reverse = True)
    print(leaderboard)
    
  for i in range(placings):
    await ctx.send( str(i+1) +". "+str(leaderboard[i][1])+" - "+str(leaderboard[i][0]))

# clear downloads
#@bot.command(help="- clears the downloaded images")
#async def clear(ctx):
 # print("clear")
 # try:
  #  shutil.rmtree(r'/home/runner/downloads')
  #  await ctx.send("Cleared downloads.")
 # except FileNotFoundError:
  #  await ctx.send("Already cleared."

# Test command - for testing purposes only
@bot.command(help="- test command")
async def test(ctx):
  for bird in birdList:
    index = birdList.index(bird)
    sciBird = sciBirdList[index]
    print (sciBird, "- " + bird)
  print(sciBirdList)
  print(birdList)

######
# ERROR CHECKING
######

## Global error checking
@bot.event
async def on_command_error(ctx, error):
  print("Error: "+str(error))
  if isinstance(error, commands.CommandOnCooldown): # send cooldown
    await ctx.send("**Cooldown.** Try again after "+str(round(error.retry_after))+" s.", delete_after=3.0)
  
  elif isinstance(error, commands.CommandNotFound):
    await ctx.send("Sorry, the command was not found.")
    
  elif isinstance(error, commands.MissingRequiredArgument):
    await ctx.send("This command requires an argument!")
  
  elif isinstance(error, commands.CommandInvokeError):
    if isinstance(error.original, KeyError):
      if ctx.channel.id in dictOfServers:
        await ctx.send("**An unexpected KeyError has occurred.** \n*Please log this message in #feedback* \n**Error:** " + str(error))
      else:
        dictOfServers[ctx.channel.id] = ["", True, "", True, 0]
        await ctx.send("Ok, setup! I'm all ready to use!")
        await ctx.send("Please run that command again.")

  else:
    print("uncaught")
    await ctx.send("**An uncaught error has occurred.** \n*Please log this message in #feedback.* \n**Error:**  " + str(error))
    raise error

# Actually run the bot
token = os.getenv("token")
bot.run(token)
