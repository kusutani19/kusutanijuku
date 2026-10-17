from PIL import Image,ImageDraw,ImageFont
from pathlib import Path
from functools import lru_cache
import numpy as np,json,math,random,subprocess,wave
import argparse, shutil
parser=argparse.ArgumentParser(description="Render a retro RPG school-results video from JSON")
parser.add_argument("--data",type=Path,required=True)
parser.add_argument("--output-dir",type=Path,required=True)
parser.add_argument("--font",type=Path,default=Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"))
parser.add_argument("--mono-font",type=Path,default=Path("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"))
args=parser.parse_args()
config=json.loads(args.data.read_text(encoding="utf-8"))
brand=config.get("brand","クスタニ塾")
heading=config.get("heading","KUSUTANI QUEST")
maximum=config.get("max_score",500)
intro=config.get("intro_seconds",3);card=config.get("card_seconds",3);outro=config.get("outro_seconds",4)
if not isinstance(brand,str) or not 1<=len(brand)<=20:parser.error("brand must be 1–20 characters")
if not isinstance(heading,str) or not 1<=len(heading)<=32:parser.error("heading must be 1–32 characters")
if type(maximum) is not int or not 1<=maximum<=9999:parser.error("max_score must be an integer in 1–9999")
if any(type(v) not in (int,float) or not 1<=v<=30 for v in (intro,card,outro)):parser.error("durations must be 1–30 seconds")
rows=config.get("results")
if not isinstance(rows,list) or not 1<=len(rows)<=100:parser.error("results must contain 1–100 entries")
data=[]
for i,row in enumerate(rows,1):
 if not isinstance(row,dict):parser.error(f"result {i}: expected an object")
 for key in ("school","grade","test"):
  if not isinstance(row.get(key),str) or not 1<=len(row[key])<=30:parser.error(f"result {i}: {key} must be 1–30 characters")
 if type(row.get("score")) is not int or not 0<=row["score"]<=maximum:parser.error(f"result {i}: score outside 0–{maximum}")
 if type(row.get("personal_best",False)) is not bool:parser.error(f"result {i}: personal_best must be boolean")
 data.append((row["school"],row["grade"],row["test"],row["score"],row.get("personal_best",False)))
if not shutil.which("ffmpeg"):parser.error("ffmpeg is required")
for path in (args.font,args.mono_font):
 if not path.is_file():parser.error(f"font missing: {path}; pass --font / --mono-font")
O=args.output_dir;O.mkdir(parents=True,exist_ok=True)
W,H=540,960;FPS=30;N=len(data);END=intro+N*card;D=END+outro
@lru_cache(None)
def ft(sz,mono=False):return ImageFont.truetype(str(args.mono_font if mono else args.font),sz,index=0)
def fit(s,sz,width,mono=False):
 while sz>8 and ft(sz,mono).getlength(s)>width:sz-=1
 f=ft(sz,mono)
 if f.getlength(s)>width:raise ValueError(f"Text too wide: {s}")
 return f
def center(d,y,s,sz,col='#ffffff',mono=False):
 f=fit(s,sz,W-60,mono);b=d.textbbox((0,0),s,font=f);d.text(((W-b[2])/2,y),s,font=f,fill=col)
def avatar(d,x,y,c):
 u=6;d.rectangle((x,y,x+u*8-1,y+u*8-1),fill=c)
 for a,b in [(2,2),(5,2)]:d.rectangle((x+a*u,y+b*u,x+(a+1)*u-1,y+(b+2)*u-1),fill='#152137')
 d.rectangle((x+2*u,y+6*u,x+6*u-1,y+7*u-1),fill='#152137')
y,x=np.mgrid[0:H,0:W];glow=np.exp(-(((x-270)/280)**2+((y-250)/370)**2));a=np.zeros((H,W,3),dtype=np.uint8);a[:,:,0]=5+glow*7;a[:,:,1]=7+glow*7;a[:,:,2]=19+glow*27;bg=Image.fromarray(a)
rng=random.Random(3);stars=[(rng.randrange(W),rng.randrange(H),rng.random()*6) for _ in range(24)]
colors=['#82f389','#80d0ff','#f098d4','#ffcd73','#b392ff','#7af1da']
cards=[]
for k in range(N+2):
 im=bg.copy();d=ImageDraw.Draw(im);center(d,37,heading,18,'#d0d6ed',True)
 if k==0:
  center(d,325,brand,39,'#fff179');center(d,390,'せいせきクエスト',31,'#fff179');center(d,458,'定期テスト・実力テストの記録',22)
  center(d,515,f'{N}例の努力と、その成果。',20,'#b6bed5');center(d,605,'▶ START',22,'#92f9a2',True)
 elif k==N+1:
  center(d,315,'つづく…',26,'#ffed81');center(d,409,brand,51);center(d,511,'次の自己ベストへ！',25,'#fff18b');center(d,582,'キミの挑戦を、応援します。',20,'#b6c5df')
 else:
  school,grade,test,score,best=data[k-1]
  # Double-line battle result window, as in the reference.
  edge='#ffe978' if best else '#d9dffb';fill='#282108' if best else '#11183f'
  d.rectangle((29,303,511,708),fill=fill,outline='#3c426d',width=2);d.rectangle((33,307,507,704),outline=edge,width=2);d.rectangle((37,311,503,700),outline='#545531' if best else '#373d68',width=1)
  d.rectangle((160,284,380,327),fill='#fff29a',outline='#fffbd6',width=2)
  center(d,289,'自己ベスト更新！' if best else '高得点 獲得！',24,'#242318')
  avatar(d,63,361,colors[(k-1)%len(colors)])
  d.text((130,347),'がっこう・がくねん',font=ft(13),fill='#a9b0c7');d.text((130,370),school+' '+grade+'年生',font=fit(school+' '+grade+'年生',29,355),fill='#ffffff')
  d.text((62,434),test,font=fit(test,21,420),fill='#d4d9e7');d.text((62,477),f'5教科合計 ／ {maximum}点満点',font=ft(16),fill='#c4c6ca')
  d.text((62,589),'EXP',font=ft(15,True),fill='#ffeb77' if best else '#8ef29d')
  d.rectangle((106,594,479,611),outline='#d9dce9',width=2);d.rectangle((110,598,475,607),fill='#171b2a')
  d.line((60,635,481,635),fill='#999272' if best else '#585c7e',width=1)
  d.text((62,650),'自己ベスト更新！ おめでとう！' if best else '見事な高得点！ おめでとう！',font=ft(21),fill='#fff18a' if best else '#f2f3ff')
  center(d,749,f'成績の記録  {k:02d} / {N:02d}',17,'#b5bdd7')
 cards.append(im)
# Original chiptune arpeggios and result jingles.
sr=44100;n=round(sr*D);audio=np.zeros(n,dtype=np.float32)
def tone(st,dur,fr,vol):
 i=int(st*sr);cnt=min(int(dur*sr),n-i)
 if cnt<=0:return
 t=np.arange(cnt)/sr;env=np.minimum(t/.008,1)*np.minimum((cnt/sr-t)/.04,1)*np.exp(-t*1.4)
 # Finite harmonics give a soft retro tone without harsh clipping.
 audio[i:i+cnt]+=vol*env*(np.sin(2*np.pi*fr*t)+np.sin(2*np.pi*fr*3*t)/5+np.sin(2*np.pi*fr*5*t)/12)
chords=[[261.63,329.63,392],[220,261.63,329.63],[174.61,220,261.63],[196,246.94,293.66]]
for b in range(math.ceil(D*4)):
 chord=chords[(b//16)%4];tone(b*.25,.22,chord[b%3],.065)
 if b%4==0:tone(b*.25,.72,chord[0]/2,.07)
for k in range(N):
 for j,fr in enumerate([523.25,659.25,783.99,1046.5]):tone(intro+k*card+.12+j*.09,.3,fr,.055)
audio*=np.minimum(np.arange(n)/(sr*.4),1)*np.minimum((n-np.arange(n))/(sr*1.5),1)
with wave.open(str(O/'quest_music.wav'),'wb') as out:out.setparams((1,2,sr,0,'NONE','not compressed'));out.writeframes((np.clip(audio,-.95,.95)*32767).astype('<i2').tobytes())
p=subprocess.Popen(['ffmpeg','-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s','540x960','-r',str(FPS),'-i','-','-i',str(O/'quest_music.wav'),'-vf','scale=1080:1920:flags=neighbor','-c:v','libx264','-preset','fast','-crf','20','-pix_fmt','yuv420p','-c:a','aac','-b:a','160k','-movflags','+faststart','-shortest',str(O/'results.mp4')],stdin=subprocess.PIPE)
for frame in range(round(D*FPS)):
 t=frame/FPS
 if t<intro:k=0;local=t;length=intro
 elif t<END:k=min(N,1+int((t-intro)//card));local=(t-intro)%card;length=card
 else:k=N+1;local=t-END;length=outro
 im=cards[k].copy();d=ImageDraw.Draw(im)
 for sx,sy,phase in stars:
  if 28<sx<512 and 280<sy<805:continue
  v=int(110+75*math.sin(t*1.4+phase));d.rectangle((sx,sy,sx+1,sy+1),fill=(v,v,int(v*.8)))
 if 1<=k<=N:
  best=data[k-1][4];score=data[k-1][3];prog=min(1,local/.55);val=round(score*(1-(1-prog)**3))
  d.text((61,499),str(val),font=fit(str(val),66,195),fill='#fff082');d.text((265,546),'点',font=ft(22),fill='#f2eddd')
  bar=int(365*(score/maximum)*prog)
  if bar>0:
   d.rectangle((110,598,110+bar,607),fill='#f7db65' if best else '#77e772');d.line((110,598,110+bar,598),fill='#fff4a9' if best else '#c1ffc4',width=2)
  if int(local*3)%2==0:d.polygon([(480,682),(492,682),(486,689)],fill='#fff073')
  if best:
   # Explicit Japanese badge; no unprovided previous score or gain is invented.
   d.rectangle((343,252,518,285),fill='#ffe777',outline='#ed4b4b',width=2);d.text((353,257),'自己ベスト更新！',font=ft(18),fill='#b62a22')
 else:
  if int(local*2)%2==0:center(d,873,'▼ つぎの冒険へ',16,'#8d9ebd')
 # Quick fade, preserving the reference's brisk card-to-card rhythm.
 fade=min(1,local/.10,(length-local)/.10)
 if fade<1:im=Image.blend(Image.new('RGB',(W,H)),im,max(0,fade))
 if frame==round((intro+min(.8,card*.5))*FPS):im.resize((1080,1920),Image.Resampling.NEAREST).save(O/'quest_preview.jpg')
 if frame==round((END+outro*.5)*FPS):im.resize((1080,1920),Image.Resampling.NEAREST).save(O/'quest_end.jpg')
 p.stdin.write(im.tobytes())
 if frame%(FPS*10)==0:print(f'render {t:.0f}/{D}s',flush=True)
p.stdin.close();assert p.wait()==0
(O/'manifest.json').write_text(json.dumps({'brand':brand,'results':N,'personal_bests':sum(r[4] for r in data),'duration_seconds':D,'width':1080,'height':1920,'fps':FPS,'data':config},ensure_ascii=False,indent=2),encoding='utf-8')
print(f'DONE: {O / "results.mp4"}',flush=True)
