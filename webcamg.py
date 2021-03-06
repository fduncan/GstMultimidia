# -*- coding: utf-8 -*-
#!/usr/bin/env python
#Author: Ana Queila, Jeferson e Uesle

import sys, os


##### Importa a Biblioteca GTK+ #####
import pygtk
pygtk.require("2.0")
import gtk
import gtk.glade
    
### Importa a Biblioteca Gstreamer ###

import pygst
pygst.require('0.10')
import gst

class Grava():

	def on_record_clicked(self, event):
		if self.pipe.get_state()[1] == gst.STATE_NULL:
			filepath = self.fcb.get_filename()
			name = self.entry.get_text()+".avi"
			if os.path.isdir(filepath):
				self.sink.set_property("location", filepath +"/"+ name)
				self.pipe.set_state(gst.STATE_PLAYING)
			
	def on_stop_clicked(self, event):
		if self.pipe.get_state()[1] == gst.STATE_PLAYING:
			self.pipe.set_state(gst.STATE_NULL)
			
	def on_finish_clicked(self, widget, data=None):
		self.janela.hide_all()

	arquivoglade = "webcamG.glade"
	
	def __init__ (self):
		
		
		#criando builder
		builder = gtk.Builder()
		#carregando arquivo do glade no builder
		builder.add_from_file(self.__class__.arquivoglade)
		
		#carregando janela
		self.janela = builder.get_object("janela")
		#Carregando o DrawingArea
		self.movie_window = builder.get_object("movie_window")
		self.fcb =  builder.get_object("filechooserbutton1")
		self.entry = builder.get_object("entry1")
		#conectando os sinais
		#builder.connect_signals(handle.__dict__)
		builder.connect_signals(self)
		#Exibe toda interface
		self.janela.show_all()

		self.pipe = gst.Pipeline("MyPlayer")
		videosrc = gst.element_factory_make("v4l2src", "v4l")
		videorate = gst.element_factory_make("videorate","videorate")
		caps = gst.Caps("video/x-raw-yuv, framerate=(fraction)30/1 ")
		capsfilter = gst.element_factory_make("capsfilter", "filter")
		capsfilter.set_property("caps", caps)
		tvid = gst.element_factory_make("tee","tvid")
		colorspace = gst.element_factory_make("ffmpegcolorspace", "colorspace")
		enc = gst.element_factory_make("jpegenc", "enc")
		vidqueue = gst.element_factory_make("queue","vidqueue")
		audqueue = gst.element_factory_make("queue","audqueue")
		queue = gst.element_factory_make("queue","queue")
		audiosrc = gst.element_factory_make("alsasrc","audiosrc")
		convert = gst.element_factory_make("audioconvert","convert")
		audiorate = gst.element_factory_make("audiorate")
		acaps = gst.Caps("audio/x-raw-int ,width=16,depth=16,rate=44100,channels=2,signed=true")
		acapsfilter = gst.element_factory_make("capsfilter","afilter")
		acapsfilter.set_property("caps", acaps)
		mux = gst.element_factory_make("avimux", "mux")
		squeue = gst.element_factory_make("queue","squeue")
		tsink = gst.element_factory_make("xvimagesink","tsink")
		tsink.set_property("synchronous", False)
		self.sink = gst.element_factory_make("filesink", "sink")
		
		
		self.pipe.add(videosrc, videorate, capsfilter, tvid, acapsfilter, audiorate, tsink, colorspace, enc,vidqueue)
		self.pipe.add(audiosrc, convert, audqueue)
		self.pipe.add(squeue, mux, self.sink)
		
		gst.element_link_many(videosrc, videorate, capsfilter, tvid, tsink)
		gst.element_link_many( tvid, colorspace, enc, vidqueue, mux)
		gst.element_link_many(audiosrc, convert, audiorate, acapsfilter, audqueue, mux)
		gst.element_link_many(mux, self.sink)
		
		bus = self.pipe.get_bus()
		bus.add_signal_watch()
		bus.enable_sync_message_emission()
		bus.connect("message", self.on_message)
		bus.connect("sync-message::element", self.on_sync_message)
		
		self.movie_window.modify_bg(gtk.STATE_NORMAL, gtk.gdk.Color(red=0, green=0, blue=0, pixel=65535))
		
		gtk.gdk.threads_init()
		gtk.main()

	gtk.gdk.notify_startup_complete()


	def on_message(self, bus, message):
		t = message.type
		print t
		if t == gst.MESSAGE_EOS:
			self.pipe.set_state(gst.STATE_NULL)

		elif t == gst.MESSAGE_ERROR:
			err, debug = message.parse_error()
			print "Error: %s" % err, debug
			self.pipe.set_state(gst.STATE_NULL)
			

	def on_sync_message(self, bus, message):
		if message.structure is None:
			return
		message_name = message.structure.get_name()
		if message_name == "prepare-xwindow-id":
			# Assign the viewport
			imagesink = message.src
			imagesink.set_property("force-aspect-ratio", True)
			gtk.gdk.threads_enter()
			imagesink.set_xwindow_id(self.movie_window.window.xid)
			gtk.gdk.threads_leave()
			
