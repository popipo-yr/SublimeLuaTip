#-----------------------------------------------------------------------------------
# LuaTip Sublime Text Plugin
# Author: popipo
# Version: 1.0
# Description: Sublime text autocomplete improvements: 
#				- showing lua methods with parameters
#-----------------------------------------------------------------------------------
import sublime, sublime_plugin, os, re, threading
import codecs
from os.path import basename

#
#Just Enum
#
class TipType:
    objfunc = 0 # function ABC:ABC()
    norfunc = 1 # function ABC.ABC()
    jutfunc = 2 # function ABC()
    other   = 3 # others
    
#
# Tip Class
#
class Tip:
	_name = ""
	_signature = ""
	_filename = ""
	_tipType =  -1
	def __init__(self, name, signature, filename, hintStr, className, tipType):
		self._name = name
		self._filename = filename;
		self._signature = signature
		self._hintStr = hintStr
		self._className = className
		self._tipType = tipType
	def name(self):
		return self._name
	def signature(self):
		return self._signature
	def filename(self):
		return self._filename
	def hintStr(self):
		return self._hintStr
	def className(self):
		return self._className
	def tipType(self):
		return self._tipType

#
# LuaTip Class
#
class LuaTip:
	_functions = []
	_curfunctions = []
	_requires = []

	MAX_WORD_SIZE = 100
	MAX_FUNC_SIZE = 50

	def clearCur(self):
		self._curfunctions = []
	def clear(self):
		self._functions = []
		self._requires = []
	def addFunc(self, name, signature, filename, hintStr, className, tipType):
		self._functions.append(Tip(name, signature, filename, hintStr, className, tipType))
	def addFuncCur(self, name, signature, filename, hintStr, className, tipType):
		self._curfunctions.append(Tip(name, signature, filename, hintStr, className, tipType))
	def addRequire(self,hintStr):
		self._requires.append(hintStr)	
	def get_autocomplete_list_helper(self, word, whichFuncs):
		autocomplete_list = []
		for method_obj in whichFuncs:
			if (word in method_obj.name()) or (word in method_obj.className()) or (word in method_obj.hintStr()):
				method_str_to_append = method_obj.name() + '(' + method_obj.signature()+ ')'
				
				if method_obj.className() != "":
					if method_obj.tipType() == TipType.objfunc:
						method_str_to_append = method_obj.className() + ":" + method_str_to_append
					elif method_obj.tipType() == TipType.norfunc:
						method_str_to_append = method_obj.className() + "." + method_str_to_append

				if method_obj.name() == "" and (method_obj.signature() == "") and (method_obj.tipType() == TipType.other):
					method_str_to_append = method_obj.className() + "    ^-^"
					
				method_file_location = method_obj.filename();
				method_str_hint = method_obj.hintStr()
				
				autocomplete_list.append((method_str_to_append + '\t' + method_file_location,
					method_str_hint))	
		return autocomplete_list
	def get_autocomplete_require_helper(self, word):
		autocomplete_list = []
		requireset = set(self._requires)
		for requirestr in requireset:
			if (word in requirestr):				
				autocomplete_list.append((requirestr,requirestr))	
		return autocomplete_list	

	def get_autocomplete_list(self, word):
		autocomplete_list = []
		autocomplete_list += self.get_autocomplete_list_helper(word, self._functions)
		autocomplete_list += self.get_autocomplete_list_helper(word, self._curfunctions)
		autocomplete_list += self.get_autocomplete_require_helper(word)
		autocomplete_list.append(("---luatip" + '\t' + "xs","---luatip")) 
		return autocomplete_list


def is_lua_file(filename):
	return '.lua' in filename

#
# LuaTip Collector Thread
#
class LuaTipCollectorThread(threading.Thread):
	
	def __init__(self, collector, open_folder_arr, timeout_seconds):  
		self.collector = collector
		self.timeout = timeout_seconds
		self.open_folder_arr = open_folder_arr
		threading.Thread.__init__(self)

	#
	# Get all method signatures
	#
	def save_method_signature(self, file_name):
		file_lines = codecs.open(file_name,'rU','utf-8')
		for line in file_lines:
			if "luatip" in line:
				matches = re.search('---luatip\s*(\w+):(\w+)\s*\((.*)\)', line)
				matches2 = re.search('---luatip\s*(\w+)\s*\((.*)\)', line)
				matches3 = re.search('---luatip\s*(\w+).(\w+)\s*\((.*)\)', line)
				matches4 = re.search('---luatip\s*(\w+)', line)

				preHint = ""
				methodName = ""
				endHint = ")"
				tipType = -1

				m = None
				if matches != None and (len(matches.group(2)) < self.collector.MAX_FUNC_SIZE and len(matches.group(3)) < self.collector.MAX_FUNC_SIZE):
					m = matches
					signIndex = 3
					className = matches.group(1)
					methodName = m.group(signIndex - 1)
					preHint = className + ":" + methodName +"("
					tipType = TipType.objfunc

				elif matches2 != None and (len(matches2.group(1)) < self.collector.MAX_FUNC_SIZE and len(matches2.group(2)) < self.collector.MAX_FUNC_SIZE):
					m = matches2
					signIndex = 2
					className = ""
					methodName = m.group(signIndex - 1)
					preHint =  methodName +"("
					tipType = TipType.jutfunc

				elif matches3 != None and (len(matches3.group(2)) < self.collector.MAX_FUNC_SIZE and len(matches3.group(3)) < self.collector.MAX_FUNC_SIZE):
					m = matches3
					signIndex = 3
					className = matches3.group(1)
					methodName = m.group(signIndex - 1)
					preHint = className + "." + methodName +"("
					tipType = TipType.norfunc	

				elif matches4 != None: #and (len(matches3.group(0)) < self.collector.MAX_FUNC_SIZE and len(matches3.group(1)) < self.collector.MAX_FUNC_SIZE):
					className = matches4.group(1)
					tipType = TipType.other
					self.collector.addFunc("", "", basename(file_name), className, className, tipType)
				 	continue

				if m != None:
					paramLists = m.group(signIndex)
					params = paramLists.split(',')
					stHint = ""
					count = 1
					for param in params:
						stHint = stHint + "${" + str(count) + ":" + param + "}"
						if count != len(params):
							stHint += ","
						count = count + 1

					
					stHint = preHint + stHint + endHint

					self.collector.addFunc(m.group(signIndex-1), m.group(signIndex), basename(file_name), stHint, className, tipType)
			if "require" in line:
				matches = re.search('require\((.*)\)', line)
				if None != matches:
					stHint = "require(" + matches.group(1) + ")"
					self.collector.addRequire(stHint)
	#
	# Get luascript files paths
	#
	def get_luascript_file(self, dir_name, *args):
		fileList = []
		for file in os.listdir(dir_name):
			dirfile = os.path.join(dir_name, file)
			if os.path.isfile(dirfile):
				fileName, fileExtension = os.path.splitext(dirfile)
				if fileExtension == ".lua":
					fileList.append(dirfile)
			elif os.path.isdir(dirfile):
				fileList += self.get_luascript_file(dirfile, *args)
		return fileList

	def run(self):
		for folder in self.open_folder_arr:
			luafiles = self.get_luascript_file(folder)
			for file_name in luafiles:
				self.save_method_signature(file_name)

	def stop(self):
		if self.isAlive():
			self._Thread__stop()

#
# CurTip Collector Thread
#
class CurTipCollectorThread(threading.Thread):
	
	def __init__(self, collector, open_file, timeout_seconds):  
		self.collector = collector
		self.timeout = timeout_seconds
		self.open_file = open_file
		threading.Thread.__init__(self)

	#
	# Get all method signatures
	#
	def save_method_signature(self, file_name):
		file_lines = codecs.open(file_name,'rU','utf-8')
		for line in file_lines:
			if "function" in line:
				matches = re.search('function\s*(\w+):(\w+)\s*\((.*)\)', line)
				matches2 = re.search('function\s*(\w+)\s*\((.*)\)', line)
				matches3 = re.search('function\s*(\w+).(\w+)\s*\((.*)\)', line)

				preHint = ""
				methodName = ""
				endHint = ")"
				tipType = -1

				m = None
				if matches != None and (len(matches.group(2)) < self.collector.MAX_FUNC_SIZE and len(matches.group(3)) < self.collector.MAX_FUNC_SIZE):
					m = matches
					signIndex = 3
					className = matches.group(1)
					methodName = m.group(signIndex - 1)
					preHint = className + ":" + methodName +"("
					tipType = TipType.objfunc

				elif matches2 != None and (len(matches2.group(1)) < self.collector.MAX_FUNC_SIZE and len(matches2.group(2)) < self.collector.MAX_FUNC_SIZE):
					m = matches2
					signIndex = 2
					className = ""
					methodName = m.group(signIndex - 1)
					preHint =  methodName +"("
					tipType = TipType.jutfunc

				elif matches3 != None and (len(matches3.group(2)) < self.collector.MAX_FUNC_SIZE and len(matches3.group(3)) < self.collector.MAX_FUNC_SIZE):
					m = matches3
					signIndex = 3
					className = matches3.group(1)
					methodName = m.group(signIndex - 1)
					preHint = className + "." + methodName +"("
					tipType = TipType.norfunc

				if m != None:
					paramLists = m.group(signIndex)
					params = paramLists.split(',')
					stHint = ""
					count = 1
					for param in params:
						stHint = stHint + "${" + str(count) + ":" + param + "}"
						if count != len(params):
							stHint += ","
						count = count + 1

					
					stHint = preHint + stHint + endHint

					self.collector.addFuncCur(m.group(signIndex-1), m.group(signIndex), basename(file_name), stHint, className, tipType)


	def run(self):
		self.save_method_signature(self.open_file)

	def stop(self):
		if self.isAlive():
			self._Thread__stop()
#
# LuaTip Collector Class
#
class LuaTipCollector (LuaTip, sublime_plugin.EventListener):

	_collector_thread = None
	_curTipCollector_thread = None

	#
	# Invoked when user save a file
	#
	def on_post_save(self, view):
		self.on_post_save_helper(view)
		self.on_activated_helper(view)
	#
	# Change autocomplete suggestions
	#
	def on_query_completions(self, view, prefix, locations):
		current_file = view.file_name()
		completions = []
		compl_default = []
		compl_full = []

		if prefix.upper().find("CC") == 0:
			return 0

		if is_lua_file(current_file):

			completions.extend(self.get_autocomplete_list(prefix))
			
			for c in view.extract_completions(prefix):
				compl_default.append((c,c))

        	compl_default = list(set(compl_default)) 
        	compl_full.extend(compl_default)
        	compl_full.extend(completions)       	
        	compl_full.sort()

        	return (compl_full, sublime.INHIBIT_WORD_COMPLETIONS |
        		sublime.INHIBIT_EXPLICIT_COMPLETIONS)
			
		return None

		
	#
	#Activate view
	# 
	def on_activated(self, view):
		self.on_activated_helper(view)
		self.on_post_save_helper(view)
	#
	# Helper
	#
	def on_post_save_helper(self, view):
		self.clear()
		if None != view.window(): 
			open_folder_arr = view.window().folders()
			#if None != open_folder_arr:
			if self._collector_thread != None:
				self._collector_thread.stop()
			self._collector_thread = LuaTipCollectorThread(self, open_folder_arr, 30)
			self._collector_thread.start()

	#
	# Helper
	#
	def on_activated_helper(self, view):
		current_file = view.file_name()
		if None != current_file and is_lua_file(current_file):
			self.clearCur()
			if self._curTipCollector_thread != None:
				self._curTipCollector_thread.stop()
			self._curTipCollector_thread = CurTipCollectorThread(self, current_file, 30)
			self._curTipCollector_thread.start()
			
				

