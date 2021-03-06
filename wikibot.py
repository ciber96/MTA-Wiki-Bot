#! /usr/bin/env python
from bs4 import BeautifulSoup
import urllib2
import irc.bot
import irc.strings
import re
from irc.client import ip_numstr_to_quad, ip_quad_to_numstr
f = open("password.txt","r")
nspass = f.readline().rstrip()
f.close()


channels = "#mta.scripting,#mta.dev"
nick = "wikibot"
server = "irc.gtanet.com"
port = 6667
nspass = nspass

definitionData = {
    "Clientside event" : { 'color': 4, 'name' : 'Client Event' },
    "Serverside event" : { 'color': 7, 'name' : 'Client Event' },
    "Client-only function" : { 'color': 4, 'name' : 'Client' },
    "Server-only function" : { 'color': 7, 'name' : 'Server' },
    "Shared function" : { 'color': 12, 'name' : 'Both' }
}

#keyword:ircColor
keywords = {
"matrix":3,
"vector2":3,
"vector3":3,
"vector4":3,
"ban":3,
"blip":3,
"bool":3,
"boolean":3,
"callback":3,
"client":3,
"colcircle":3,
"colcube":3,
"colshape":3,
"colsphere":3,
"colsquare":3,
"coltube":3,
"console":3,
"element":3,
"float":3,
"int":3,
"marker":3,
"object":3,
"ped":3,
"pickup":3,
"player":3,
"radararea":3,
"remoteclient":3,
"resource":3,
"string":3,
"table":3,
"team":3,
"textdisplay":3,
"textitem":3,
"vehicle":3,
"xmlnode":3,
"false":6,
"true":6,
"nil":6,
"function":6,
}

puns = {
"\\":10,
"\"":10,
"'":10,
"-":10,
"+":10,
"=":10,
"[":10,
"]":10,
"(":10,
")":10,
"*":10,
"/":10,
"^":10,
",":10,
}

class WikiBot(irc.bot.SingleServerIRCBot):
    def __init__(self, channels, nickname, server, port=6667):
        irc.bot.SingleServerIRCBot.__init__(self, [(server, port)], nickname, nickname)
        self.channel = channels

    def on_nicknameinuse(self, c, e):
        c.nick(c.get_nickname() + "_")

    def on_welcome(self, c, e):
		joinC = self.channel.split(",")
		for ch in joinC:
			c.join(ch)
		c.privmsg("nickserv","identify "+nspass)

    def on_privmsg(self, c, e):
        self.do_command(e, e.arguments[0].split(), e.source.nick)

    def on_pubmsg(self, c, e):
        self.do_command(e, e.arguments[0].split(), None)
        return

    def on_dccmsg(self, c, e):
        return

    def on_dccchat(self, c, e):
        return

    def do_command(self, e, args, privMessager):
        target = privMessager if privMessager else channel
        c = self.connection
        cmd = args[0]
        if cmd == "!wiki" and len(args)>1:
            wiki(c,args,target)

global stack;
stack = 0;
def wiki(c,args,target):
    global stack;
    if stack == 6:
        stack = 0;
        return;
    stack += 1
     
    fnName = args[1];
    url = 'http://wiki.multitheftauto.com/wiki/'+fnName
    try:
        page = urllib2.urlopen(url)
    except urllib2.URLError, err: #To-do: Try again
        print(urllib2.URLError, err)
        return
    try:
        page = page.read()
    except urllib2.URLError, err:
        print(urllib2.URLError, err)
        return
        
    # Let's strip out examples onwards if we've found them            
    exampleStart = page.find('<span class="mw-headline" id="Example">')
    if exampleStart != -1:
        page = page[:exampleStart]
    
    soup = BeautifulSoup(page, 'html.parser')           
    #Scan for deprecated functions
    deprecated = soup.find(text=re.compile('This function is deprecated. This means that its use is discouraged and that it might not exist in future versions.'))
    if deprecated > 0:
        a = deprecated.parent.parent.parent.find("a")
        if a:
            args[1] = a.get('href').replace('/wiki/','')
            return wiki(c,args,target)
    
    for meta in soup.find_all('meta'):
        if meta.get('name') == 'headingclass':
            fnName = soup.select("h1")[0].string
            fnName = fnName[0].lower() + fnName[1:]                   
            fnType = meta.get('data-subcaption')
            if definitionData.get(fnType):
                keywords[fnName] = definitionData[fnType]['color']
            else:
                continue
            
            codeList = soup.select("pre.lang-lua")
            if codeList[0]:
                #Try and find a server syntax
                serverCodeList = soup.select("div.serverContent pre.lang-lua")
                for code in serverCodeList:
                    fnTypeNow = "Server-only function" if fnType.find("function") != -1 else "Serverside event"
                    outputSyntax(c,fnName,fnTypeNow,code.string,target)
                
                #Then a client syntax
                clientCodeList = soup.select("div.clientContent pre.lang-lua")
                for code in clientCodeList:
                    fnTypeNow = "Client-only function" if fnType.find("function") != -1 else "Clientside event"
                    outputSyntax(c,fnName,fnTypeNow,code.string,target)
                
                #Fall back to content without a <section/> tag
                if len(serverCodeList) == 0 and len(clientCodeList) == 0:
                    for code in codeList:
                        outputSyntax (c,fnName,fnType,code.string,target)
            
            print("\x02"+url+"\x02")
            c.privmsg(target,"\x02"+url+"\x02")
            stack = 0
            return

def main():
    import sys
    bot = WikiBot(channels, nick, server, port)
    bot.start()
    
def cleanString(str):
    return (" ").join(str.replace("\t",' ').replace("\n",'').replace("\r",'').split())
    
def reg_repl(m):
    color = "%02d" %keywords[m.group(0)]
    return "\x03" + color + m.group(0) + "\x03"
    
def syntaxHighlight(str,fnName,color):
    for k in keywords:
        str = re.sub(r"\b%s\b"%k,reg_repl,str)   
    
    for p in puns:
        color = "%02d" % puns[p]
        str = str.replace(p,"\x03" + color + p + "\x03\x0F")
    
    return str
        

def outputSyntax(c,fnName,fnType,text,target):
    text = cleanString(text)
    color = "%02d" % definitionData[fnType]['color']
    text = syntaxHighlight(text,fnName,color)
    output = "\x02\x03"+color+definitionData[fnType]['name']+"\x02\x03\x0F"
    output += ": " + text
    print(output)
    try:
        c.privmsg(target,output)    
    except Exception,e: 
        print str(e)

if __name__ == "__main__":
    main()
