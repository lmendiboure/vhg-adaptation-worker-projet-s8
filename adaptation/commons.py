__author__ = 'nherbaut'
import subprocess
import math
import os 
import re
import tempfile
import shutil
import uuid
import sys
import zipfile
import requests
import subprocess
import unirest

# Need to be changed, add the adaptation folder directory to the system path
sys.path.append(os.path.abspath("adaptation"))

# celery import
from celery import Celery, chord

# config import
from settings import config

# media info wrapper import
from pymediainfo import MediaInfo

# lxml import to edit dash playlist
from lxml import etree as LXML

# context helpers
from context import get_transcoded_folder, get_transcoded_file, get_dash_folder, get_dash_mpd_file_path, get_yuv_file, get_description_folder, get_mp4_description_folder, get_description_zip_folder, get_dash_mpd_file_folder, get_postProcessor_path,get_welsenc_path,get_layer_path, get_plus_description_folder,get_plus_mp4_description_folder, get_plus_dash_folder, get_plus_dash_mpd_file_path, get_description_plus_zip_folder, get_mpd_zip_folder

# main app for celery, configuration is in separate settings.ini file
app = Celery('tasks')


# inject settings into celery
app.config_from_object('adaptation.settings')

def run_background(*args):
    try: 
        code = subprocess.check_call(*args, shell=True)
    except subprocess.CalledProcessError:
        print "Error"

@app.task
def compute_quantification_parameters(*args):
	bitrate = args[0]
	if bitrate <= 500:
		min_quant = 200
		max_quant = 400
		in_quant = 300
	if  500 < bitrate <= 1000:
		min_quant = 40
		max_quant = 90
		in_quant = 55
	if  1000 < bitrate <=2000:
		min_quant = 25
		max_quant = 75
		in_quant = 40
	if 2000 < bitrate <= 3000:
		min_quant = 10
		max_quant = 60
		in_quant = 30
	if 3000 < bitrate <=4000:
		min_quant = 5
		max_quant = 40
		in_quant = 15
	if bitrate > 4000:
		min_quant = 0
		max_quant = 25
		in_quant = 1
	context={"min_qp": min_quant, "max_qp": max_quant, "in_qp": in_quant}
	return  context 


@app.task(bind=True)
def notify(*args, **kwargs):
    self = args[0]
    context = args[1]

    main_task_id = kwargs["main_task_id"]
    if "complete" in kwargs and kwargs["complete"]:
        self.update_state(main_task_id, state="COMPLETE")

    return context


@app.task()
def image_processing(src, dest):
    print "(------------"
    random_uuid = uuid.uuid4().hex
    context={"original_file": src, "folder_out":config["folder_out"]+ dest + "/", "id": random_uuid}
    
    if not os.path.exists(context['folder_out']):
        os.makedirs(context['folder_out'])
    
    ext = src.split('.');
    ext = ext[len(ext)-1]

    media_info = MediaInfo.parse(context["original_file"])

    for track in media_info.tracks:
	width = track.width
	print width

    extralarge = 1382
    large = 992
    medium = 768
    small = 480

    ffargsoriginal = "ffmpeg -i " + src + " -vf scale=" + str(width) +":-1 " + context["folder_out"] + "original.jpg"
    
    if width < extralarge:
        ffargsextralarge = "ln -s " + context["folder_out"] + "original.jpg" + " " + context["folder_out"] + "extralarge.jpg"
    else:
        ffargsextralarge = "ffmpeg -i " + src + " -vf scale=" + str(extralarge) +":-1 " + context["folder_out"] + "extralarge.jpg"
    if width < large:
        ffargslarge = "ln -s " + context["folder_out"] + "original.jpg" + " " + context["folder_out"] + "large.jpg"
    else:
        ffargslarge = "ffmpeg -i " + src + " -vf scale=" + str(large) + ":-1 " + context["folder_out"] + "large.jpg"
    if width < medium:
        ffargsmedium = "ln -s " + context["folder_out"] + "original.jpg" + " " + context["folder_out"] + "medium.jpg"
    else:
        ffargsmedium = "ffmpeg -i " + src + " -vf scale=" + str(medium) + ":-1 " + context["folder_out"] + "medium.jpg"
    if width < small:
        ffargssmall = "ln -s " + context["folder_out"] + "original.jpg" + " " + context["folder_out"] + "small.jpg"
    else:
        ffargssmall = "ffmpeg -i " + src + " -vf scale=" + str(small) + ":-1 " + context["folder_out"] + "small.jpg"


    run_background(ffargsoriginal)
    run_background(ffargsextralarge)
    run_background(ffargslarge)
    run_background(ffargsmedium)
    run_background(ffargssmall)



@app.task()
def ddo(src, dest, videoID,ListID, lowBitrate,midBitrate, highBitrate, changeFrameRate, resolution, desNum,managerAddr,storageAddr,transcodingAddr):
    try:
        encode_workflow(src, dest, videoID, ListID, lowBitrate, midBitrate, highBitrate, changeFrameRate, resolution, desNum,managerAddr,storageAddr,transcodingAddr)
    except:
        print "Error while encoding_workflow"
        raise



@app.task(bind=True)
def encode_workflow(self, src, dest,videoID,ListID, lowBitrate, midBitrate, highBitrate, changeFrameRate, resolution, desNum,managerAddr,storageAddr,transcodingAddr):
    main_task_id = self.request.id
    print "(------------"
    print main_task_id
    random_uuid = uuid.uuid4().hex
    context={"original_file": src, "folder_out":config["folder_out"]+ dest, "videoID":videoID, "ListID":ListID, "id": random_uuid, "bitrateList":{lowBitrate,midBitrate,highBitrate}, "lowBitrate":lowBitrate,"midBitrate":midBitrate,"highBitrate":highBitrate, "resolution":resolution, "desNum": desNum, "changeFrameRate":changeFrameRate,"managerAddr":managerAddr,"storageAddr":storageAddr,"transcodingAddr":transcodingAddr}
    if os.path.exists(context['folder_out']):
    	shutil.rmtree(context["folder_out"])
    context = get_video_size(context=context)
    context = get_video_length(context)
    context = get_video_thumbnail(context)
    context = create_yuv_file(context)
    context = compute_target_size(context, target_height=resolution)
    context = transcode(context)
    context = create_descriptions(context)
    context = create_mp4_description(context)
    context = chunk_dash(context, segtime=4) #Warning : segtime is already set in transcode.s(), but not in the same context
    context = create_description_zip(context)
    context = create_mpd_zip(context)
    #context = edit_dash_playlist(context)
    #notify.s(complete=True, main_task_id=main_task_id))
    inform_the_storage(context)	
    if (ListID != ""): # If this value is not equal to "" it means that all the videos of the list have been transcoded : the list ID is sent to the manager
    	inform_the_manager(context)
    print "Trancoding of " + str(videoID) + " done"
@app.task
# def get_video_size(input_file):
def get_video_size(*args, **kwargs):
    '''
    use mediainfo to compute the video size
    '''
    print args, kwargs
    context = kwargs["context"]
    media_info = MediaInfo.parse(context["original_file"])
    for track in media_info.tracks:
        if track.track_type == 'Video':
            print "video is %d, %d" % (track.height, track.width)
            context["track_width"] = track.width
            context["track_height"] = track.height
            return context
    raise AssertionError("failed to read video info from " + context["original_file"])

@app.task
def get_video_length(*args,**kwargs):
	context = args[0]
	tmpf = tempfile.NamedTemporaryFile()
	os.system("ffmpeg -i \"%s\" 2> %s" % (context["original_file"], tmpf.name))
	lines = tmpf.readlines()
	tmpf.close()	
	result = {}
	for l in lines:
		l = l.strip()
		if l.startswith('Duration'):
			result = re.search('Duration: (.*?),', l).group(0).split(':',1)[1].strip(' ,')
			result = result.split(":")
	length = int(result[0])*3600 + int(result[1])*60 + float(result[2])
	length = math.ceil(length)
	length = int(length)
	length = str(length)
	response = unirest.post(context["transcodingAddr"]+context["videoID"], params = length)
	return context

@app.task
# def compute_target_size(original_height, original_width, target_height):
def compute_target_size(*args, **kwargs):
    '''
    compute the new size for the video
    '''
    context = args[0]
    context["target_height"] = kwargs['target_height']

    print args, kwargs
    context["target_width"] = math.trunc(
        float(context["target_height"]) / context["track_height"] * context["track_width"] / 2) * 2
    return context

@app.task
# def get_video_thumbnail(input_file):
def get_video_thumbnail(*args, **kwargs):
    '''
    create image from video
    '''
    # print args, kwargs
    context = args[0]

    if not os.path.exists(context['folder_out']):
        os.makedirs(context['folder_out'])

    ffargs = "ffmpeg -i " + context["original_file"] + " -vcodec mjpeg -vframes 1 -an -f rawvideo -ss `ffmpeg -i " + context["original_file"] + " 2>&1 | grep Duration | awk '{print $2}' | tr -d , | awk -F ':' '{print $3/2}'` " + context["folder_out"] + "/thumbnail.jpg"
    print ffargs
    run_background(ffargs)
    return context

@app.task
# def create_yuv_file(file_in, folder_out)
def create_yuv_file(*args,**kwargs):
      context = args[0]
      if not os.path.exists(get_transcoded_folder(context)):
      	os.makedirs(get_transcoded_folder(context))
      run_background("ffmpeg -i " + context["original_file"] + " -vcodec rawvideo -pix_fmt yuv420p " + get_yuv_file(context))
      return context 
     

@app.task
# def transcode(file_in, folder_out, dimensions, bitrate_list):
def transcode(*args):
    '''
    transcode the video to mp4 format
    '''
    # print args, kwargs
    context = args[0]
    for bitrate in context["bitrateList"]:
    	parameters = compute_quantification_parameters(bitrate)
    	if not os.path.exists(get_transcoded_folder(context)):
        	os.makedirs(get_transcoded_folder(context))
    	args = get_welsenc_path(context)+ " -org " + get_yuv_file(context) + " -bf " + get_transcoded_file(context,bitrate) + " -sw " + str(context["track_width"]) + " -sh " + str(context["track_height"]) +" -tarb " + str(bitrate) + " -minqp " + str(parameters["min_qp"]) + " -maxqp " + str(parameters["max_qp"]) + " -ltarb " + get_layer_path(context) + " " + str(bitrate) + " -lqp " + get_layer_path(context) + " " + str(parameters["in_qp"]) + " -dw " + get_layer_path(context) + " " + str(context["target_width"]) + " -dh " + get_layer_path(context) + " " + str(context["target_height"])
    	run_background(args) 
    	print args

    return context

@app.task
def create_descriptions(*args):
	context  = args[0]
	if not os.path.exists(get_description_folder(context)):
        	os.makedirs(get_description_folder(context))

	if not os.path.exists(get_plus_description_folder(context)):
        	os.makedirs(get_plus_description_folder(context))

	args = get_postProcessor_path(context)+" " + get_transcoded_folder(context) + "/" + str(context["lowBitrate"])+".h264 " + get_transcoded_folder(context) + "/" + str(context["highBitrate"])+".h264 " + get_description_folder(context) +" " + str(context["changeFrameRate"]) + " " + str(context["desNum"])
	plus_args = get_postProcessor_path(context)+" " + get_transcoded_folder(context) + "/" + str(context["midBitrate"])+".h264 " +  get_transcoded_folder(context) + "/" + str(context["midBitrate"])+".h264 " + get_transcoded_folder(context) + "/" + str(context["highBitrate"])+".h264 " + get_plus_description_folder(context) +" " + str(context["changeFrameRate"]) + " " + str(context["desNum"])

	run_background(args)
	run_background(plus_args)	
	print args
	print(plus_args)
	shutil.rmtree(get_transcoded_folder(context))
	return context  


@app.task
def create_mp4_description(*args):
	i =1
	context = args[0]
	
	while i<= int(context["desNum"]):
		if not os.path.exists(get_mp4_description_folder(context,i)):
        		os.makedirs(get_mp4_description_folder(context,i))
		if not os.path.exists(get_plus_mp4_description_folder(context,i)):
        		os.makedirs(get_plus_mp4_description_folder(context,i))
		args = "ffmpeg -f h264 -i "+ get_description_folder(context)+"/Description_"+ str(i) +".h264 -vcodec copy " +get_mp4_description_folder(context,i)+"/Description_"+str(i)+".mp4"
		plus_args = "ffmpeg -f h264 -i "+ get_plus_description_folder(context)+"/Description_"+ str(i) +".h264 -vcodec copy " +get_plus_mp4_description_folder(context,i)+"/Description_plus_"+str(i)+".mp4"
		run_background(plus_args)
		run_background(args)
		i+=1
	shutil.rmtree(get_description_folder(context))
	shutil.rmtree(get_plus_description_folder(context))
	return context

@app.task
# def chunk_dash(files_in, folder_out):
def chunk_dash(*args, **kwargs):
	'''
	create dash chunks for every video in the transcoded folder
	'''
	# print args, kwargs
	context = args[0]
	segtime = kwargs['segtime']
	i =1

	if not os.path.exists(get_dash_mpd_file_folder(context)):
		os.makedirs(get_dash_mpd_file_folder(context))

	while i<=int(context["desNum"]):	
		if not os.path.exists(get_dash_folder(context,i)):
			os.makedirs(get_dash_folder(context,i))

		if not os.path.exists(get_plus_dash_folder(context,i)):
			os.makedirs(get_plus_dash_folder(context,i))

		args = "MP4Box -dash " + str(segtime) + "000 -profile live "
		files_in = [os.path.join(get_mp4_description_folder(context,i), f) for f in os.listdir(get_mp4_description_folder(context,i))]
		for j in range(0, len(files_in)):
			args += files_in[j] + "#video:id=v" + str(j)
		args += " -out " + get_dash_mpd_file_path(context,i)
		print args
		plus_args = "MP4Box -dash " + str(segtime) + "000 -profile live "
		files_in_plus = [os.path.join(get_plus_mp4_description_folder(context,i), f) for f in os.listdir(get_plus_mp4_description_folder(context,i))]
		for j in range(0, len(files_in_plus)):
			plus_args += files_in_plus[j] + "#video:id=v" + str(j)
		plus_args += " -out " + get_plus_dash_mpd_file_path(context,i)
		print plus_args
		run_background(args)
		run_background(plus_args)
		i +=1
	k=1
	while k<=int(context["desNum"]):
		shutil.move(get_dash_mpd_file_path(context,k),get_dash_mpd_file_folder(context))
		shutil.move(get_plus_dash_mpd_file_path(context,k),get_dash_mpd_file_folder(context))   
		k+=1
	return context

@app.task
def create_description_zip(*args):
	context = args[0]	
	i = 1;
	while i<=int(context["desNum"]):
		zip_file = zipfile.ZipFile(get_description_zip_folder(context,i), 'w', zipfile.ZIP_DEFLATED)
		zip_file_plus = zipfile.ZipFile(get_description_plus_zip_folder(context,i), 'w', zipfile.ZIP_DEFLATED)
	   	files_in = [os.path.join(get_dash_folder(context,i),f) for f in os.listdir(get_dash_folder(context,i))]
		files_in_plus = [os.path.join(get_plus_dash_folder(context,i),f) for f in os.listdir(get_plus_dash_folder(context,i))]
		for j in range(0,len(files_in)):
			zip_file.write(files_in[j],os.path.basename(files_in[j]))
			zip_file_plus.write(files_in_plus[j],os.path.basename(files_in_plus[j]))
		shutil.rmtree(get_mp4_description_folder(context,i))
		shutil.rmtree(get_dash_folder(context,i))
		shutil.rmtree(get_plus_mp4_description_folder(context,i))
		shutil.rmtree(get_plus_dash_folder(context,i))
		i+=1
	return context

@app.task
def create_mpd_zip(*args):
	context = args[0]
	zip_file = zipfile.ZipFile(get_mpd_zip_folder(context), 'w', zipfile.ZIP_DEFLATED)
	files_in = [os.path.join(get_dash_mpd_file_folder(context),f) for f in os.listdir(get_dash_mpd_file_folder(context))]
	for j in range(0,len(files_in)):
		zip_file.write(files_in[j],os.path.basename(files_in[j]))
	shutil.rmtree(get_dash_mpd_file_folder(context))
	return context
@app.task
def edit_dash_playlist(*args, **kwards):
    '''
    create dash chunks for every video in the transcoded folder
    '''
    # print args, kwargs
    context = args[0]

    tree = LXML.parse(get_dash_mpd_file_path(context))
    root = tree.getroot()
    # Namespace map
    nsmap = root.nsmap.get(None)

    #Function to find all the BaseURL
    find_baseurl = LXML.ETXPath("//{%s}BaseURL" % nsmap)
    results = find_baseurl(root)
    audio_file = results[-1].text
    results[-1].text = "audio/" + results[-1].text # Warning : This is quite dirty ! We suppose the last element is the only audio element
    tree.write(get_dash_mpd_file_path(context))

    #Move audio files into audio directory
    os.makedirs(os.path.join(get_dash_folder(context), "audio"))
    shutil.move(os.path.join(get_dash_folder(context), audio_file), os.path.join(get_dash_folder(context), "audio", audio_file))

    #Create .htaccess for apache
    f = open(os.path.join(get_dash_folder(context), "audio", ".htaccess"),"w")
    f.write("AddType audio/mp4 .mp4 \n")
    f.close()
    return context

@app.task 
def inform_the_storage(*args):
	context = args[0]
	response = unirest.get(context["storageAddr"]+context["videoID"])
	result = response.code
	#if int(result)<400:
	#	clean_useless_folders(context)
	print "storage response : " + str(result)
@app.task 
def inform_the_manager(*args):
	context = args[0]
	response = unirest.post(context["managerAddr"], params = context["ListID"])
	print "manager response : " + str(response.code)
@app.task
# def add_playlist_footer(playlist_folder):
def clean_useless_folders(*args):
	'''
	delete encoding folder
	'''
	# print args, kwargs
	context = args[0]
	shutil.rmtree(context["folder_out"])
