import json 
from sentence_transformers import SentenceTransformer
import numpy as np
import os


CURRENT_DIRECTORY =os.path.join(os.getcwd(),r'data pipeline\data processing workflow')
CONTENT_FILTERING_FOLDER_LOCATION = os.path.join(CURRENT_DIRECTORY,r'content_filtering_results')


DATA_LOCATION = os.path.join(CURRENT_DIRECTORY,r'content_filtering_data.json')

def content_filtering(data_file_location=DATA_LOCATION):
    
    #collect name and present task
    name = input("Please write your name:")
    description = "Dummy description of the task"

    #load data
    data_file = open(data_file_location, 'r')
    res_dict = json.load(data_file)

    keys = []
    embeddings = []
    for key in res_dict:
        res = res_dict[key]
        description = res['description']
        if  description == "[deleted]" or description== "[removed]":
            continue
        else:
            keys.append(key)
            embeddings.append(res['embedding'])

    #compute similarities
    model = SentenceTransformer("avsolatorio/GIST-large-Embedding-v0")
    embeddings = np.array(embeddings)
    similarities = model.similarity(embeddings,embeddings)

    #distribute them on buckets based on average similarity ratings

    bins = {"85-90":[],"80-85":[],"75-80":[],"70-75":[],"65-70":[],"60-65":[],"55-60":[],"50-55":[]}

    for res_index in range(len(keys)):

        top5_v,top5_i= similarities[res_index].topk(k=5)

        avg_sim=top5_v[1:].mean().item()
        res_key = keys[res_index]
        similar_res_indexes = [keys[idx] for idx in top5_i[1:].tolist()]
        similar_scores = top5_v[1:].tolist()
        baseline_res = res_dict[res_key]
        if avg_sim >0.85:
            bins["85-90"].append((baseline_res,similar_res_indexes,similar_scores))
        elif avg_sim>0.80:
            bins["80-85"].append((baseline_res,similar_res_indexes,similar_scores))
        elif avg_sim>0.75:
            bins["75-80"].append((baseline_res,similar_res_indexes,similar_scores))
        elif avg_sim>0.70:
            bins["70-75"].append((baseline_res,similar_res_indexes,similar_scores))
        elif avg_sim>0.65:
            bins["65-70"].append((baseline_res,similar_res_indexes,similar_scores))
        elif avg_sim>0.60:
            bins["60-65"].append((baseline_res,similar_res_indexes,similar_scores))
        elif avg_sim>0.55:
            bins["55-60"].append((baseline_res,similar_res_indexes,similar_scores))
        elif avg_sim>0.50:
            bins["50-55"].append((baseline_res,similar_res_indexes,similar_scores))

    #this 2 functions ensures that there is a small chance that we get 
    #a resource that is too similar or not enough similar
    def sample_sim_res_index(mean=2.5,sigma = 1):
        sampled_idx = np.random.normal(size=sigma, loc=mean, scale=1)

        while sampled_idx<1 or sampled_idx>5:
            sampled_idx = np.random.normal(size=sigma, loc=mean, scale=1)
        sampled_idx  = int(sampled_idx)
        return sampled_idx-1

    def sample_res(buckets):
        sampled_res = []
        for bin in buckets:
            size = len(buckets[bin])
            sampled_res_idx = np.random.randint(0,size,1).item()
            sampled_sim_res_idx = sample_sim_res_index()
            baseline_res = buckets[bin][sampled_res_idx][0]
            similar_res_idx = buckets[bin][sampled_res_idx][1][sampled_sim_res_idx]
            similar_res_score = buckets[bin][sampled_res_idx][2][sampled_sim_res_idx]
            sampled_res.append( { 'bin':bin,'baseline_res':baseline_res,'similar_res_idx':similar_res_idx,'similar_res_score':similar_res_score } )
            
        return sampled_res

    results_file_location = os.path.join(CONTENT_FILTERING_FOLDER_LOCATION,name+'_content_filtering.json')

    results_file = open(results_file_location,'w')
    results = {}


    #recommending in pairs of 2 and collecting feedback about recommendation
    #at every level of similarity score (from mean 50 to mean 90)
    for bin_rec_sample in sample_res(bins):
        #presenting baseline

        bin = bin_rec_sample['bin']
        baseline_res = bin_rec_sample["baseline_res"]
        print(f'bin : {bin}')
        print(f'baseline:')
        print(f'title: {baseline_res["title"]}')
        print(f'url: {baseline_res["url"]}')
        print(f'description: {baseline_res["description"]}')

        baseline_score = float(input('How much did this post make you see things trough a new perspective?:'))

        #presenting recommendation
        print(f'recommendation:')
        rec_idx = bin_rec_sample["similar_res_idx"]
        rec_res = res_dict[rec_idx]
        print(f'title: { rec_res["title"]}')
        print(f'url: { rec_res["url"]}')
        print(f'description: { rec_res["description"]}')
        rec_sim_score = bin_rec_sample["similar_res_score"]
        print(f'similarity: {rec_sim_score}')
        
        rec_score = float(input('How much did this recommended post make you see things trough a new perspective?:'))
        relevance_score = float(input('On a scale of 1-5, how much would you agree with the statement  \"The recommend post was relevant to the first post, but presented the subject through a novel perspective\":'))

        bin_result = {'similarity_score':rec_sim_score, 'baseline_score':baseline_score,'recommendation_score':rec_score,'relevance_score':relevance_score,'baseline_res':baseline_res,'recommendation':rec_res}

        results[bin] = bin_result

        print('-'*100)


    json.dump(results,results_file)

content_filtering()