function setCookie(e,o,t){var n=new Date;n.setTime(n.getTime()+24*t*60*60*1e3);var i="expires="+n.toUTCString();document.cookie=e+"="+o+";"+i+";path=/"}function getCookie(e){for(var o=e+"=",t=decodeURIComponent(document.cookie).split(";"),n=0;n<t.length;n++){for(var i=t[n];" "==i.charAt(0);)i=i.substring(1);if(0==i.indexOf(o))return i.substring(o.length,i.length)}return""}function unblockVideos(){document.querySelectorAll(".video_wrapper .video_trigger").forEach(function(e){e.style.display="none";for(var o=0;o<e.parentNode.childNodes.length;o++){var t=e.parentNode.childNodes[o];if("video_layer"==t.className){t.style.display="block";for(var n=0;n<t.childNodes.length;n++){var i=t.childNodes[n];if("iframe"==i.tagName.toLowerCase()){var r=e.getAttribute("data-source");i.src="https://www.youtube-nocookie.com/embed/"+r+"?controls=1&showinfo=0&autoplay=0&mute=0"}}}}})}document.addEventListener("DOMContentLoaded",function(){1==getCookie("youtube-consent")?unblockVideos():document.querySelectorAll(".video_wrapper .video_trigger .video-btn").forEach(function(e){e.addEventListener("click",function(){setCookie("youtube-consent",1,365),unblockVideos()})})});