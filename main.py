from flask import Flask, session, request, redirect

import numpy as np

import json
import os

app = Flask(__name__)

tasks=[]
def load_tasks():
    global tasks
    with open("tasks.json", "r") as f:
        tasks = json.load(f)
def get_tasks():
    if len(tasks)==0:
        load_tasks()
    return tasks

@app.route("/test")
def test():
    return '''
<script>

document.addEventListener("keydown",(event)=> {
  var name = event.key;
  var code = event.code;
  // Alert the key name and key code on keydown
  alert(`Key pressed ${name} \r\n Key code value: ${code}`);
},false);

</script>



'''

@app.route("/debug")
def debug():
    load_tasks()
    max_score=[]
    avg_score=[]
    all_score=[]
    for i,t in enumerate(tasks):
        scores=[tt["value"] for tt in t[1:]]
        max_score.append(max(scores))
        avg_score.append(np.median(scores))
        all_score.append(scores)
    def random_eval():
        q=[np.random.choice(qq) for qq in all_score]
        return sum(q)
    from simplestat import statinf
    rand=[random_eval() for _ in range(10000)]
    from plt import plt
    plt.hist(rand,bins=20)
    plt.savefig("hist.png")
    return f'''
<h1>Debug</h1>
<h2>Max</h2>
{sum(max_score)}
<h2>Avg</h2>
{sum(avg_score)}
<h2>All</h2>
{statinf(rand)}
'''



def outer(func):
    def f(*args, **kwargs):
        r=func(*args, **kwargs)
        return r
    return f

def has_user():
    if "user" in session:
        return session["user"]
    return None

def has_task():
    if "task" in session:
        return session["task"]
    return None

def set_user(user):
    session["user"] = user

def remove_user():
    if "user" in session:
        del session["user"]

def set_task(task):
    session["task"] = task

def remove_task():
    if "task" in session:
        del session["task"]


def no_user():
    return f'''
        <h1>Who are you</h1>
        <form action="/setuser" method="GET">
            <input type="text" name="name"><br>
            <input type="submit">
        </form>
'''
def no_task():
    return f'''
        <h1>Who are you evaluating?</h1>
        <form action="/settask" method="GET">
            <input type="text" name="name"><br>
            <input type="submit">
        </form>
'''

@app.route("/setuser",methods=["GET"])
def site_set_user():
    name=request.args.get("name")
    set_user(name)
    print(name)

    return redirect("/")

@app.route("/settask",methods=["GET"])
def site_set_task():
    name=request.args.get("name")
    set_task(name)
    print(name)

    return redirect("/")

def show_option(i,s,q,tid):
    col={0:"#FF6060",1:"white",2:"#75FF60"}
    col=col[q]
    return f'''
<a href="/answer/{tid}/{i}" style="color:black">
    <div style="background-color: {col};font-size:x-large;text-align:center;foreground-color:black;">
        {s}
    </div>
</a>
'''

    return f'<span style="color:{col}">{s}</span>'

def show_task(tid):
    task=get_tasks()[tid]
    phrase=task[0]
    task=task[1:]
    
    opts=[t["string"] for t in task]
    quals=[int(t["qual"]) for t in task]
    ret= "<br>".join([show_option(i,s,q,tid) for i,(s,q) in enumerate(zip(opts,quals))])
    return '''
<script>

document.addEventListener("keydown",(event)=> {
  var name = event.key;
  if(name=="1"){
    window.location.href="/answer/{tid}/0";
  }
  if(name=="2"){
    window.location.href="/answer/{tid}/1";
  }
  if(name=="3"){
    window.location.href="/answer/{tid}/2";
  }
},false);

</script>

'''.replace("{tid}",str(tid))+f'''
<h1>{tid+1}: {phrase}</h1>
<br>
{ret}
'''

def task_id(i):
    return f"task_{i}"

def next_task():
    for i,t in enumerate(get_tasks()):
        acn=task_id(i)
        if acn in session:
            continue
        return i
    return None

def remove_tasks():
    for i,t in enumerate(get_tasks()):
        acn=task_id(i)
        if acn in session:
            del session[acn]

def finish():
    user=has_user()
    task=has_task()
    if user is None or task is None:return "something went wrong, what are you?"
    res=[]
    for i,t in enumerate(get_tasks()):
        acn=task_id(i)
        if not acn in session:
            return "you should finish my friend"
        res.append(int(session[acn]))
    tasks=get_tasks()
    vals=[t[r+1]["value"] for r,t in zip(res,tasks)]
    score=sum(vals)
    outp={"user":user,"task":task,"values":vals,"res":res,"score":score}
    os.makedirs("results",exist_ok=True)
    with open(f"results/{user}_{task}.json","w") as f:
        json.dump(outp,f,indent=2)
    remove_tasks()
    remove_task()
    return f'''
thanks. your score is {score}
<br>
<a href="/">Another Round?</a>

'''


@app.route("/answer/<tid>/<aid>")
def answer(tid,aid):
    session[task_id(tid)]=aid
    return redirect("/")
@app.route('/')
@outer
def index():
    if not has_user():return no_user()
    if not has_task():return no_task()
    nex=next_task()
    if nex is None:return finish()
    return show_task(nex)


app.secret_key="12"

#app.run(host='0.0.0.0', port=81)
app.run(port=8000)


