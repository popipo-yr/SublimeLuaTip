SublimeLuaTip

SublimeLuaTip - Sublime text 2 plugin for lua autocomplete - changed from MySignature and wtyqm's changing

the plugin maps all your lua methods of the form function xxx() {} , function ooo.xxx() {} and function ooo:xxx() {} in current open   lua file, and all "---luatip ABC" ,"---luatip ABC:ABC()", "---luatip ABC.ABC()"."---luatip ABC()" in other lua files.

so,if want to tip one lua method when you edit other file,just like this:

---luatip tipme()
function  tipme()
end 

---luatip xxx.tipme()
function  xxx.tipme()
end 

---luatip xxx:tipme()
function  xxx:tipme()
end 

also,if  want to tip a var,just like this:
---luatip xxx

Install  Clone the repository in your Sublime Text Packages directory, located somewhere in user's "Home" directory.

Enjoy it
