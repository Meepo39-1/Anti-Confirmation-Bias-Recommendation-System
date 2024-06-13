import json
import os
from pathlib import Path
import collections

#SESSION_PATH = Anti Confirmation Bias Recommendation System\\data pipeline\\data processing workflow\\data processing session
SESSION_PATH =os.path.join(os.getcwd(), 'data processing session')
LOADED_RESOURCES_PATH = os.path.join(SESSION_PATH,'resources_info.txt')

#dicts for resources and title, shall be used for matrix factorization#

#key: title, value: id
res_id = collections.defaultdict()
#key: id, value: resource object:  
id_res = collections.defaultdict()
#key: username, value: id
user_id = collections.defaultdict()
#key:id, value: user object
id_user = collections.defaultdict()

description = {}

#titles of resources which shall be used for extracting descriptions (for content filtering)#
search_titles = set()

#titles which had no description found#
not_found_titles = set()

# resource loading functions #
def load_resources_from_raw_delta_logs(out_file_path = LOADED_RESOURCES_PATH, min_num_interactions=0):

    ''' Loads resources from raw_delta_log_submissions.txt 
        
        Extracts title,url and feedback 
        
        Saves resources with a minimum number of ratings into res_id and id_res 
        
        min_num_interactions -> treshold for minimum number of ratings

        out_file_path -> file location of generated resources file
    '''
    global res_id, id_res,user_id,id_user
    # restore dictionary values 
    res_id = collections.defaultdict()
    id_res = collections.defaultdict()
    user_id = collections.defaultdict()
    id_user = collections.defaultdict()
     
    delta_logs_file_path = os.path.join(os.getcwd(),'raw_delta_log_submissions.txt')

  
    res_file_path = out_file_path

    def get_OP_from_delta_log(body):

        '''
            Find original poster (OP) from post description body

            Returns: username (string)
        '''
        
        start_index = body.find('/u/') +3
        end_index = body[start_index:].find('\n\n')

        return body[start_index:start_index+end_index]
    
    def get_users_who_got_delta_from_OP(text):

        '''
            Extract usernames of users who negatively rated the post from text

            Returns: username list(list of strings)
        '''
        
        KEY_PHRASE_START = '1 delta from OP to /u/'
        KEY_PHRASE_START_OFFSET = len(KEY_PHRASE_START)
        KEY_PHRASE_END = ' for'

        list_users = []

        while text.find(KEY_PHRASE_START)!=-1:

            #print(text.find(KEY_PHRASE_START))
            start_user_name = text.find(KEY_PHRASE_START)+KEY_PHRASE_START_OFFSET
            end_user_name = text.find(KEY_PHRASE_END)
            list_users.append(text[start_user_name:end_user_name])
            text = text[end_user_name+1:]
            #print(text)

        return list_users
    
    def get_users_who_got_delta_from_OTHERS(text):

        '''
            Extract usernames of users who positively rated the post
            but were not the original poster (OP)

            Returns: username list(list of strings)
        '''

        list_users = []

        CUT_PHRASE = 'Deltas from Other Users'
        FST_USER_KEY_PHRASE_START = '1 delta from /u/'
        FST_USER_KEY_PHRASE_END = ' to /u/'
        SND_USER_KEY_PHRASE_END = ' for '
        #cutting irrelevant text
        text = text[text.find(CUT_PHRASE)+len(CUT_PHRASE):]
        #print(text)
        
        while text.find(FST_USER_KEY_PHRASE_START)!=-1:

            first_user = text[text.find(FST_USER_KEY_PHRASE_START)+ len(FST_USER_KEY_PHRASE_START):text.find(FST_USER_KEY_PHRASE_END)]
    
            #getting past first user
            text = text[text.find(FST_USER_KEY_PHRASE_END)+len(FST_USER_KEY_PHRASE_END):]
            #extracting the second user
            #text = text[text.find(FST_USER_KEY_PHRASE_END)+len(FST_USER_KEY_PHRASE_END):]
            second_user = text[:text.find(SND_USER_KEY_PHRASE_END)]

            list_users.append((first_user,second_user))

            #cutting second user and going back to the loop
            text = text[text.find(second_user)+1:]

        return list_users
    
    def extract_feedback_from_post(body):
        '''
            Extract all users who rated the post

            Returns: (positive feedback users, negative feedback users) (tuple of lists of strings)
        
        '''
        positive_feedback_op = []
        if len(get_users_who_got_delta_from_OP(body))>0:
            positive_feedback_op = [get_OP_from_delta_log(body)]

        negative_feedback_op_users = get_users_who_got_delta_from_OP(body)

        try:
            positive_feedback_others_users, negative_feedback_others_users = get_users_who_got_delta_from_OTHERS(body)
            positive_feedback_others_users = set(positive_feedback_others_users)
            negative_feedback_others_users = set(negative_feedback_others_users)
        except:
            if len(get_users_who_got_delta_from_OTHERS(body))>0:
                positive_feedback_others_users = set([get_users_who_got_delta_from_OTHERS(body)[0][0]])
                negative_feedback_others_users = set([get_users_who_got_delta_from_OTHERS(body)[0][1]])
            else:
                positive_feedback_others_users = set()
                negative_feedback_others_users = set()

        pos_feedback_users = list(positive_feedback_others_users) + positive_feedback_op
        neg_feedback_users = list(negative_feedback_others_users) + negative_feedback_op_users
        
        return (pos_feedback_users,neg_feedback_users)
    def extract_delta_log_titles_urls_interactions(line,out_file,titles,urls,min_num_interactions=1,):
        '''

        Extracts resource data from text entry in the format:
            (
            title of reddit post,

             url of reddit post,

             users who rated the post postively,

             users who rated the post negatively
             )

        line -> text entry from raw_delta_log_submissions.txt 

        out_file -> file where resource data will be written

        titles -> set of previosly met titles

        urls -> set of previously met urls

        min_num_interactions -> treshold for resource data to appear in out_file
        '''

        global search_titles
        title =  clean_title(json.loads(line)['title'])
        try:
            body_text = json.loads(line)['selftext']
        except:
            body_text = json.loads(line)['body']
        
        cut_start = body_text.find('(')+1
        cut_end = body_text.find(')')
        
        if body_text[cut_start:cut_end][:len('https://www.reddit.com/')] == 'https://www.reddit.com/':
            url = body_text[cut_start:cut_end]
        else:
            url = 'https://www.reddit.com/' + body_text[cut_start:cut_end]

        if url not in urls and title not in titles:
            urls.add(url)
            titles.add(title)
            log_post = json.loads(line)
            try:
                body = log_post['selftext']
            except:
                body = log_post['body']
            
            pos_feedback_users, neg_feedback_users = extract_feedback_from_post(body)
            
            
            if len(pos_feedback_users) +len(neg_feedback_users) >= min_num_interactions: 
                title.lower() 
                #print(title)
                id = len(res_id) + 1 
                res_id[title] = id
                id_res[id] = {"title":title,'pos_feedback':pos_feedback_users,'neg_feedback':neg_feedback_users,'url':url}
                out_file.write(json.dumps({"id": id,"title":title,'pos_feedback':pos_feedback_users,'neg_feedback':neg_feedback_users,'url':url}))
                out_file.write('\n')
   
                search_titles.add(title)   

    def extract_resources_from_delta_logs_file(res_file_path,delta_logs_file_path,min_num_interactions=2,tolerance_limit=100):
        '''
        Refer to load_resources_from_raw_delta_logs

        res_file_path -> file location of generated resources

        delta_logs_file_path -> file location

        min_num_interactions -> ratings treshold for resource to be added to the file

        tolerance_limit -> if found more errors than this treshold, stop the execution
    
        '''

        global res_id
        global id_res
        id_res = collections.defaultdict()
        res_id = collections.defaultdict()
        res_file = open(res_file_path,'w',encoding="utf8")
        delta_logs_file = open(delta_logs_file_path,'r',encoding="utf8")
        titles = set()
        urls = set()
        num_exceptions  = 0
        TOLERANCE_LIMIT = tolerance_limit
        MIN_NUM_INTERACTIONS = min_num_interactions

        for line in delta_logs_file:
            try:
                extract_delta_log_titles_urls_interactions(line,res_file,titles,urls,MIN_NUM_INTERACTIONS)
            except Exception as e: 
                print(e)
                num_exceptions+=1
                if num_exceptions>TOLERANCE_LIMIT:
                    break
        res_file.close()
        delta_logs_file.close()
    extract_resources_from_delta_logs_file(res_file_path,delta_logs_file_path,min_num_interactions)

get_resource_id_errs = 0
def get_resource_id(title, fail_safely=False):
    global get_resource_id_errs 
    
    id = None
    if fail_safely:
        try:
            id = res_id[title]
        except:
            get_resource_id_errs+=1
            id = len(res_id) + 1
    else:
        id = res_id[title]
    
    return id   

def get_resource_info(id):
    return id_res[id]

def clean_title(title):
    IRELEVANT_PREFIX_LENGTH = len('Deltas awarded in \"cmv:')
    IRELEVENT_SUFIX_LENGTH = len('... ')
    new_title = title
    if title[IRELEVANT_PREFIX_LENGTH:][0]!=" ": 
    
        #litera mare, trebuie adaugat un spatiu
        new_title = title[:IRELEVANT_PREFIX_LENGTH] +" " +title[IRELEVANT_PREFIX_LENGTH:]
        #print('Adaugare Spatiu:' ,new_title)
        #print(new_title[:IRELEVANT_PREFIX_LENGTH][-2:])
        if(new_title[:IRELEVANT_PREFIX_LENGTH][-1]==' '):
            #exista :, dar e mai incolo
            if ':' in new_title[IRELEVANT_PREFIX_LENGTH:IRELEVANT_PREFIX_LENGTH+5]:
                while new_title[:IRELEVANT_PREFIX_LENGTH][-1]!=':':
                    new_title = new_title[:IRELEVANT_PREFIX_LENGTH-1] + new_title[IRELEVANT_PREFIX_LENGTH+1:]
                #print('mutare ":" la stanga: ',new_title)
            else:
                #print('Aduagat ":" ',
                new_title = new_title[:IRELEVANT_PREFIX_LENGTH-1] + ": "+ new_title[IRELEVANT_PREFIX_LENGTH+1:]

    #print(new_title)
    if new_title[-4:len(new_title)-1]=='...':
    #new_title =new_title[:-4]
        new_title = new_title[:len(new_title)-4]
    new_title = new_title[IRELEVANT_PREFIX_LENGTH:]
    if new_title[:6] == ' CMV: ':
        new_title = new_title[5:]
    
    if title[-1] == '\n':
        new_title = new_title[:len(new_title)-1]
        #count+=1
        #if count >=3750:
        #    print(line)
        #    print(new_title)
    if new_title[-1] == '"' and new_title[-2]!='"':
        new_title = new_title[:len(new_title)-1]
    else:
        #print(new_title[-1],new_title[-2])
        pass

    new_title = new_title.strip()
    new_title = new_title.replace('\u2019',"'")
    new_title = new_title.replace(r'\u201','"')
    #print(new_title)
    return new_title


# users loading functions#
def load_users(out_file=None, min_num_interactions=0):
    '''
    Extracts users with min_num_interactions ratings or more 

    Users are saved in user_id, and id_res dicts

    Notes:
      You need to run load_resources_from_raw_delta_logs() first
    '''
    res_file_path = os.path.join(LOADED_RESOURCES_PATH)
    users_file_path = os.path.join(SESSION_PATH,'users_info')

    
    def extract_int_users(res_file_path):
        res_file = open(res_file_path,'r')
        users = {}

        for line in res_file:
            res = json.loads(line)
            pos_feedback= res['pos_feedback']
            neg_feedback = res['neg_feedback']

            title = res['title']
            for user in pos_feedback:
                if user not in users:
                    users[user] = {'pos_feedback': [title],'neg_feedback':[]}
                else:
                    users[user]['pos_feedback'].append(title)

            for user in neg_feedback:
                if user not in users:
                    users[user] = {'pos_feedback': [],'neg_feedback':[title]}
                else:
                    users[user]['neg_feedback'].append(title) 
        res_file.close() 
        return users    
    def extract_high_int_users(users_file_path,users={},min_num_interactions = 2):
        users_file = open(users_file_path,'w',encoding="utf-8")
        high_int_users = set()
        global user_id
        global id_user
        #user_id = collections.defaultdict()
        for user in users.keys():
            num_poz_interactions = len(users[user]['pos_feedback'])
            num_neg_interactions = len(users[user]['neg_feedback'])
            #print(f'pos: {num_poz_interactions}, neg: {num_neg_interactions}')
            num_total_interactions = num_poz_interactions + num_neg_interactions
            if num_total_interactions>=min_num_interactions:
                user_obj ={'user':user,'num_poz_interactions':num_poz_interactions,'num_neg_interactions':num_neg_interactions,'total':num_total_interactions,'pos_feedback':users[user]['pos_feedback'],'neg_feedback':users[user]['neg_feedback'] }

                users_file.write(json.dumps(user_obj,ensure_ascii=False))
                users_file.write('\n')
                id = len(user_id) + 1
                user_id[user] = len(user_id) + 1
                id_user[id] = user_obj
                high_int_users.add(user)
        users_file.close()
        return high_int_users
    users_interactions = extract_int_users(res_file_path)
    high_int_users = extract_high_int_users(users_file_path,users_interactions,min_num_interactions=min_num_interactions)
def get_user_id(username):
    return user_id[username]
def get_username(id):
    return id_user[id]


#computing ratings functions#
def feedback_formula(num_ratings,positive=True):
    ''' 
    Given that the dataset ratings are negatively skewed, 
    the feedback formula favors positive feedback

    positive feedback = 1/2 + 1/4 +... +1/2^num_ratings
    neg_feedbcak = -( 1/2 + 1/8 + 1/16 +...+1/2^num_ratings+1)

    Why this choice?
    user colleced feedback is about changing their views about a topic
    current computed feedback is about being exposed to a novel perspective,
    since trying to "adjust" for the negative biased in dataset
    '''
    s = 0
    exp = 1
    for i in range(1,num_ratings+1):
        if positive == False and i == 2:
            exp+=1
        s = s+ 1/2**exp
        exp+=1
        
    if positive == False:

        s = -1* s
    return s

def update_feedback(ratings,res):

    ''' 
    Transform ratings from binary ("changed my mind","not changed my mind")
    to a continous value between -1("no novel perspective) and 1(mind blowingly perspective)

    ratings -> dict of previously user binary ratings
    res -> dictionary of resources data (title, url, pos_feedback_users, neg_feedback_users)
    '''
     
    for user_id in ratings.keys():
        #Modifying user ratings from  dict->list to dict->dict

        feedback = {}
        for res_id, value in ratings[user_id]:
            feedback[res_id] = value
        
        ratings[user_id] = feedback

    #Transform feedback by taking into account the number of deltas accorded for each resource
    for res_id in res.keys():
        pos_feedback = res[res_id]['pos_feedback']
        neg_feedback = res[res_id]['neg_feedback']

        new_pos_feedback = feedback_formula(len(pos_feedback))
        new_neg_feedback = feedback_formula(len(pos_feedback),positive=False)
        ''' erorrs are caused by the fact that not all users who interacted
        with the resource are in the final list of users
          (users who had at least min_interactions with other resources)'''
        for username in pos_feedback:
            try:
                user_id = get_user_id(username)
                #ratings_keys = list(ratings.keys())
                if user_id in ratings.keys():
                    ratings[user_id][res_id] = new_pos_feedback
                #print('positive feedback registered')
            except Exception as e:
                pass
                #print(f'error casued by {e}')
        for username in neg_feedback:
            try:
                user_id = get_user_id(username)
                if user_id in ratings.keys():
                    ratings[user_id][res_id] = new_neg_feedback
            except Exception as e:
                pass
                #print(f'error casued by {e}')

def compute_ratings(print_ratings = True,remove_outlier = True):

    ''' 
        Computes ratings for every user from "data processing session/users_info"
        
        remove_outlier ->boolean for removing an user that rated all resources, signaling a possible bug
        in load_resources_from_raw_delta_logs

        Note:
            You need to run load_resources_from_raw_delta_logs and load_users first

            Check update_feedback for ratings formula

        Retuns: (users dict,resources dict,ratings dict,num_interactions)

    '''

    user_fp =os.path.join(SESSION_PATH,'users_info')
    res_fp = os.path.join(SESSION_PATH,'resources_info.txt')
    user_file = open(user_fp
    ,encoding='utf-8')
    res_file = open(res_fp)
    ratings = {}
    user = {}
    res ={}

    for line in user_file:

        #extracting user data
        obj = json.loads(line)
        user_id = get_user_id(obj['user'])
        ratings[user_id] = []
        user[user_id] = obj

        #attributing numerical values to categorical data
        pos_feedback = list(map(get_resource_id,obj['pos_feedback']))
        pos_feedback = list(zip(pos_feedback,[1] * len(pos_feedback)))
    
        neg_feedback =list(map(get_resource_id,obj['neg_feedback']))
        neg_feedback = list(zip(neg_feedback,[-1] * len(neg_feedback)))
    
        #appending data to
        ratings[user_id].extend(pos_feedback)
        ratings[user_id].extend(neg_feedback)

    if remove_outlier:
        del ratings[get_user_id("")]
    for line in res_file:
        obj = json.loads(line)
        res_id = get_resource_id(obj['title'])
        res[res_id] = obj

    print(f'{len(user)} users')
    
   
   
    update_feedback(ratings,res)

    def print_ratings(ratings, ratings_file = None):

        num_interactions = 0
        extracted_ratings_fp = os.path.join(SESSION_PATH,'extracted_ratings')
        ratings_file = open(extracted_ratings_fp,'w',encoding='utf-8')
        
        unique_resources = set()

        for user_id in ratings.keys():
            for res_id,value in ratings[user_id].items():

                ratings_file.write(f'{user_id} {res_id} {value}\n')

                num_interactions +=1
                unique_resources.add(res_id)
        ratings_file.close()

        print(f'{len(unique_resources)} rated resources from initially {len(res)} loaded resources')
        print(f'{num_interactions} interactions')
        return (num_interactions,unique_resources)

    num_interactions = 0
    if print_ratings:
        num_interactions,resources = print_ratings(ratings)
        try:
            populated_percent = (num_interactions *100) / (len(user)*len(resources))
        except:
            populated_percent = 0
        print(f'feedback matrix is {populated_percent}% populated')
    return (user,resources,ratings,num_interactions)
