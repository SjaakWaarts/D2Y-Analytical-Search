from datetime import datetime
from datetime import time
from datetime import timedelta
import re
from pandas import Series, DataFrame
import pandas as pd
import json

import seeker
import app.models as models

def yes1no0(v):
    if v == 1 or v == '1' or v == 'yes':
        return 'Yes'
    if v == 0 or v == '0' or v == 'no':
        return 'No'
    return v

def yes1no2(v):
    if v == 1 or v == '1' or v == 'yes':
        return 'Yes'
    if v == 2 or v == '2' or v == 'no':
        return 'No'
    return v

def strength5(v):
    for code, values in fld_encode['strength5'].items():
        if v in values:
            answer_code = code
            return answer_code
    return v

def liking7(v):
    for code, values in fld_encode['liking7'].items():
        if v in values:
            answer_code = code
            return answer_code
    return v

def liking9(v):
    for code, values in fld_encode['liking9'].items():
        if v in values:
            answer_code = code
            return answer_code
    return v

def todate(v):
    if len(v) == 4:
        dt = datetime.strptime(v,'%Y').date()
    elif len(v) == 6:
        if v[4] in ['q','Q']:
            m = int(v[5])*3
            v = v[0:4]+str(m)
            dt = datetime.strptime(v,'%Y%m').date()
        else:
            dt = datetime.strptime(v,'%Y%m').date()
    elif len(v) == 8:
        dt = datetime.strptime(v,'%Y%m%d').date()
    return dt

fld_encode = {
    "perception"    : {"Clean" : ["2", "Clean"], "Fresh": ["3", "Fresh"], "Long lasting" : ["1", "Long lasting"]},
    "Frequency"     : {"occasionally":["Occasionally"], "regularly":["Regularly"]},
    "Gender frag"   : {"Female":["F"], "Male":["M"],"Unisex":["U"],"Other":["00OTHER"]},
    "gender"        : {"Male" : ["Male", "Man", "1", "1.00"], "Female": ["Femal", "Woman", "2", "2.00"]},
    "strength5"     : {"5 Much too Strong" : ["5"], "4 A little too Strong": ["4"],
                       "3 Just About Right" : ["3"], "2 A little too Weak": ["2"], "1 Much too Weak": ["1"]},
    "liking7"       : {"7 Like very much" : ["7"], "6 Like moderately": ["6"], "5 Like a little" : ["5"], "4 Neither like / dislike": ["4"],
                       "3 Dislike it a little" : ["3"], "2 Disike moderately": ["2"], "1 Disike very much": ["1"]},
    "liking9"       : {"9 Like Extremely" : ["9"], "8 Like Very Much": ["8"], "7 Like Moderately" : ["7"], "6 Like Slightly": ["6"], "5 Neither Like nor Dislike" : ["5"],
                       "4 Dislike Slightly": ["4"], "3 Dislike Moderately" : ["3"], "2 Dislike Very Much": ["2"], "1 Dislike Extremely": ["1"]},
    "Occasions"     : {"everyday": ["everyday"], "everyday and special": ["good for both everyday and special occasions"], "special": ["special occasions"]},
    "How discover"  : {"myself": ["I chose it myself"], "present": ["It was a present"]},
    "Season"        : {"summer": ["more for summer time"], "winter": ["more for winter time"] , "both": ["good for both summer and winter"]},
    "Wear when perfume": {"weeks" : ["A few weeks"], "months": ["A few months"], "year" : ["More than a year"], "3 years" : ["More than 3 years"], "10 years": ["More than 10 years"]},
    }




# Direct mapping of a column to a ElasticSearch field
# In case multiple columns are mapped to the same field, the one column with a value is loaded (variant for Fresh&Clean)
col2fld = {
    'resp_id'       : (["RESPID - RESPONDENT ID", "Resp No/ID", "Panelist_Code", "Consumer ID"], 'text'),
    'group_id'      : (["Group n°"], 'text'),
    #'survey'       : (["Year"], 'text'), this is derived from the file name
    #'published_date': (["Year", "Test Quarter"], 'date'),
    'stage'         : (["Stage"], 'text'),
    'country'       : (["COUNTRY - COUNTRY", "Country", "COUNTRY"], 'text'),
    'cluster'       : (["Cluster", "Choice model Cluster"], 'text'),
    'ethnics'       : (["Ethnies"], 'text'),
    'city'          : (["City", "Test City"], 'text'),
    'regions'       : (["Regions"], 'text'),
    'education'     : (["Education"], 'text'),
    'income'        : (["Income"], 'text'),
    'blindcode'     : (["Code", "Product Code", "Sample", "Blinding_Code"], 'text'),
    'brand'         : (["Brand", "Global Brand BUMO"], 'text'),
    'variant'       : (["variant", "brand used most often liquid detergent + variant", "brand used most often powder detergent + variant"], 'text'),
    'olfactive'     : (["FF", "olfactive Family"], 'text'),
    ## Fresh & Clean
    "method"        : (["Wash Method"], 'text'),
    "freshness"     : (["h9_Freshness"], 'integer'),
    "cleanliness"   : (["h9_Cleanliness"], 'integer'),
    "lastingness"   : (["h9_Long lastingness"], 'integer'),
    "intensity"     : (["j_JAR Strength", "j_Overall Strenght (5 points scale)"], 'integer'),
    'age'           : (["Age cat", "Age group", "Q17_1__Age", "Age"], 'text'),
    "product_form"  : (["Detergent format"], 'text'),
    'gender'        : (["Woman/Man", "Gender", "Q16__Gender"], 'text'),
    "perception"    : (["would you say this fragrance is"], 'text'),
    ## Global Panels
    "category"      : (["Category", "Subcategory"], 'dict', ['cat', 'subcat']),
    }


qa = {
    "affective" : {	
	    "Balanced": (["Q1__4__Clean__Cleansed__Purified_"], yes1no0),
	    "Clean": (["Q1__5__Vibrant__Active__Dynamic__Energized__"], yes1no0),
	    "Innocent": (["Q1__3__Balanced__In_harmony__Comfortable__Relaxed__Peaceful_"], yes1no0),
	    "Instinctive": (["Q2__1__When_I_would_like_to_indulge_myself_(e_g___looking_for_a_sensory_pleasure_when_eating_or_drinking__etc_)"], yes1no0),
	    "Open Minded": (["Q1__10__Unique__Original_"], yes1no0),
	    "Optimistic": (["Q1__9__Open-minded__Free__Independent__Self-sufficient__"], yes1no0),
	    "Sensual": (["Q1__8__Optimistic__Happy__"], yes1no0),
	    "Stimulated": (["Q1__7__Sensual__Sexy__Romantic__"], yes1no0),
	    "Tender": (["Q1__2__Innocent__Modest__Simple_"], yes1no0),
	    "Unique": (["Q1__11__Instinctive__Spontaneous_"], yes1no0),
	    "Vibrant": (["Q1__6__Stimulated__Up-lifted__Vivified__"], yes1no0),
    },
    "ballot" : {	
	    "Best": (["Q10_4__Best_Practices"], yes1no2),
	    "Expected": (["Q10_3__Expected_Taste"], yes1no2),
	    "Healthy": (["Q10_6__Healthy"], yes1no2),
	    "Homemade ": (["Q10_1__Homemade"], yes1no2),
	    "Ingredients": (["Q10_12__Ingredients_Fit"], yes1no2),
	    "Minimal": (["Q10_7__Minimal_Processing"], yes1no2),
	    "Natural": (["Q10_5__Natural_Ingredients"], yes1no2),
	    "Premium": (["Q10_9__Premium"], yes1no2),
	    "Recognize": (["Q10_11__Recognize_as_orange"], yes1no2),
	    "Reminiscent": (["Q10_10__Reminiscent"], yes1no2),
	    "Traditional": (["Q10_2__Traditional_Method"], yes1no2),
	    "Unique": (["Q10_8__Unique"], yes1no2),
    },
    "behavioral" : {	
	    "Comments": (["Q3__1__When_I_need_to_hydrate_myself_"], yes1no0),
	    "Hearlty": (["Q2__6__Others__please_specify"], yes1no0),
	    "Indulge": (["Q2__2__When_I_would_like_to_withdraw_from_the_routine__(e_g___taking_a_break__etc_)"], yes1no0),
	    "Others": (["Q2__6__Others__please_specify_COMMENTS"], yes1no0),
	    "Socialize": (["Q2__4__When_I'm_working_out:_playing_sports__exercising__or_working_strenuously"], yes1no0),
	    "Withdraw": (["Q2__3__When_I_would_like_to_socialize_(e_g___catching_up_with_friends__going_for_a_meal/_a_drink_with_others__etc_)"], yes1no0),
	    "Working Out": (["Q2__5__When_I_would_like_something_healthy_to_drink"], yes1no0),
    },
    "children" : {	
	    "No children home": (["No children at home"], yes1no0),
	    "Children aged 0-6": (["Child(ren) aged 0-6 years"], yes1no0),
	    "Children aged 7-16": (["Child(ren) aged 7-16 years"], yes1no0),
	    "Children aged > 16": (["Child(ren) aged more than 16 years"], yes1no0),
    },
    "concept" : {	
	    "Anti-mold fungus": (["a1_Anti-mold fungus"], yes1no0),
	    "Anti-shrinking": (["a1_Anti-shrinking"], yes1no0),
	    "Anti-wrinkle": (["a1_Anti-wrinkle"], yes1no0),
	    "Color clothes protection": (["a1_Color clothes protection"], yes1no0),
	    "Disinfectant /antibacterial effect on clothes": (["a1_Disinfectant /antibacterial effect on clothes"], yes1no0),
	    "Easy ironing": (["a1_Easy ironing"], yes1no0),
	    "Easy rinse ": (["a1_Easy rinse "], yes1no0),
	    "Environment protection": (["a1_Environment protection"], yes1no0),
	    "Extra Brightening clothes": (["a1_Extra Brightening clothes"], yes1no0),
	    "Extra Soft / caring ": (["a1_Extra Soft / caring "], yes1no0),
	    "Extra Softening effect": (["a1_Extra Softening effect"], yes1no0),
	    "Extra Stain remover effect": (["a1_Extra Stain remover effect"], yes1no0),
	    "Extra Whitening": (["a1_Extra Whitening"], yes1no0),
	    "Fast dry clothes": (["a1_Fast dry clothes"], yes1no0),
	    "Fast ironing": (["a1_Fast ironing"], yes1no0),
	    "Fragrance booster": (["a1_Fragrance booster"], yes1no0),
	    "Fresher scent": (["a1_Fresher scent"], yes1no0),
	    "Gentle on clothes": (["a1_Gentle on clothes"], yes1no0),
	    "Kill bacteria": (["a1_Kill bacteria"], yes1no0),
	    "Long lasting fragrance": (["a1_Long lasting fragrance"], yes1no0),
	    "Long lasting freshness": (["a1_Long lasting freshness"], yes1no0),
	    "Malodor elimination": (["a1_Malodor elimination"], yes1no0),
	    "None": (["a1_None"], yes1no0),
	    "Other": (["a1_Other"], yes1no0),
	    "Protect/keep shape on clothes ": (["a1_Protect/keep shape on clothes "], yes1no0),
	    "Skin protection": (["a1_Skin protection"], yes1no0),
	    "Strong scents": (["a1_Strong scents"], yes1no0),
	    "Super clean efficacy": (["a1_Super clean efficacy"], yes1no0),
    },	
    "descriptors" : {	
	    "Acidic": (["Q11__4__Acidic"], yes1no0),
	    "Artificial": (["Q11__7__Artificial"], yes1no0),
	    "Bitter": (["Q11__5__Bitter"], yes1no0),
	    "Cheap": (["Q11__3__Cheap"], yes1no0),
	    "Harsh": (["Q11__6__Harsh"], yes1no0),
	    "Just Just": (["Q11__8__Just_Made"], yes1no0),
	    "None": (["Q11__10__None_of_the_above"], yes1no0),
	    "Other": (["Q11__9__Other"], yes1no0),
	    "other": (["Q11__9__Other_COMMENTS"], yes1no0),
	    "Refreshing": (["Q11__2__Refreshing"], yes1no0),
	    "Stale": (["Q11__1__Stale"], yes1no0),
    },
    "emotion" : {	
        "Addictive": (["a1_Addictive"], yes1no0),
        "Affectionate / Loving": (["a1_Affectionate / Loving"], yes1no0),
        "Airy": ([""], yes1no0),
        "Antibacterial/Disinfecting": (["a1_Antibacterial/Disinfecting"], yes1no0),
        "Artificial/Cheap": ([""], yes1no0),
        "Artificial/Chemical": (["a1_Artificial/Chemical"], yes1no0),
        "Beautiful": (["a1_Beautiful"], yes1no0),
        "Casual": ([""], yes1no0),
        "Cheap": (["a1_Cheap"], yes1no0),
        "Classic": (["a1_Classic"], yes1no0),
        "Clean": (["a1_Clean"], yes1no0),
        "Comforting/Relaxing": ([""], yes1no0),
        "Confident": (["a1_Confident"], yes1no0),
        "Distinctive": ([""], yes1no0),
        "Distinctive / Unique": (["a1_Distinctive / Unique"], yes1no0),
        "Elegant": (["a1_Elegant"], yes1no0),
        "Elegant/ Luxurious": ([""], yes1no0),
        "Expensive/Sophisticated": ([""], yes1no0),
        "Familiar": (["a1_Familiar"], yes1no0),
        "Feminine": (["a1_Feminine"], yes1no0),
        "For Both Men And Women": ([""], yes1no0),
        "For Daytime": ([""], yes1no0),
        "For Evening/Nighttime": ([""], yes1no0),
        "For whole family": (["a1_For whole family"], yes1no0),
        "Fresh": (["a1_Fresh"], yes1no0),
        "Fresh Air / Breezy": (["a1_Fresh Air / Breezy"], yes1no0),
        "Friendly/ Outgoing": ([""], yes1no0),
        "Glamorous": (["a1_Glamorous"], yes1no0),
        "Harsh": (["a1_Harsh"], yes1no0),
        "Harsh/ Chemical": ([""], yes1no0),
        "Has Character": ([""], yes1no0),
        "Healthy": (["a1_Healthy"], yes1no0),
        "Heavy": (["a1_Heavy"], yes1no0),
        "High quality": (["a1_High quality"], yes1no0),
        "Indulgent  ": (["a1_Indulgent  "], yes1no0),
        "Innocent": (["a1_Innocent"], yes1no0),
        "Invigorating": ([""], yes1no0),
        "Light/Delicate": ([""], yes1no0),
        "Light/mild": (["a1_Light/mild"], yes1no0),
        "Luxurious/rich": (["a1_Luxurious/rich"], yes1no0),
        "Makes me feel good": (["a1_Makes me feel good"], yes1no0),
        "Masculine": (["a1_Masculine"], yes1no0),
        "Medicinal /Therapeutic": (["a1_Medicinal /Therapeutic"], yes1no0),
        "Mild": ([""], yes1no0),
        "Modern": (["a1_Modern"], yes1no0),
        "Modern/Contemporary": ([""], yes1no0),
        "Natural": (["a1_Natural"], yes1no0),
        "New / never smelled before": (["a1_New / never smelled before"], yes1no0),
        "Nostalgic / memorable": (["a1_Nostalgic / memorable"], yes1no0),
        "Nourishing / caring": (["a1_Nourishing / caring"], yes1no0),
        "Old-fashioned": (["a1_Old-fashioned"], yes1no0),
        "Outdoor": (["a1_Outdoor"], yes1no0),
        "Premium": (["a1_Premium"], yes1no0),
        "Pure": (["a1_Pure"], yes1no0),
        "Refreshing": ([""], yes1no0),
        "Rejuvenating": (["a1_Rejuvenating"], yes1no0),
        "Romantic": ([""], yes1no0),
        "Sensual": ([""], yes1no0),
        "Sexy": ([""], yes1no0),
        "Sophisticated": (["a1_Sophisticated"], yes1no0),
        "Sporty/Athletic": (["a1_Sporty/Athletic"], yes1no0),
        "Trendy": (["a1_Trendy"], yes1no0),
        "Trendy": (["a1_Youthful"], yes1no0),
        "Unforgettable": ([""], yes1no0),
        "Warm": ([""], yes1no0),
        "Well Rounded": ([""], yes1no0),
        "Youthful": ([""], yes1no0),
    },
    "hedonics" : {	
	    #"overall": (["Q4_1__Overall_Liking_"], liking9),
	    "flavor": (["Q5_1__Orange_Flavor_Liking"], liking9),
	    "strength": (["Q6_1__Orange_flavor_strength_JAR", "JAR Strength"], strength5),
	    "sweetness": (["Q7_1__Sweetness_JAR"], strength5),
	    "sourness": (["Q8_1__Sourness_JAR"], strength5),
	    "aftertaste": (["Q9_1__aftertaste_strength_JAR"], strength5),
    },	
    "liking" : {
        "_liking7": (["h7_overall_liking fragrance", "Fragrance Liking", "h7_Overall Opinion ( 7 points scale)"], liking7),
        "_liking9": (["Q4_1__Overall_Liking_"], liking9),
    },
    "mood" : {	
	    "Apathetic, Dull, Sluggish": (["a1_mood_Apathetic, Dull, Sluggish"], yes1no0),
	    "Calm, Relaxed, Tranquil": (["a1_mood_Calm, Relaxed, Tranquil"], yes1no0),
	    "Happy, Pleased, Delighted": (["a1_mood_Happy, Pleased, Delighted"], yes1no0),
	    "Irritated, Frustrated, Agitated": (["a1_mood_Irritated, Frustrated, Agitated"], yes1no0),
	    "Sad, Gloomy, Depressed": (["a1_mood_Sad, Gloomy, Depressed"], yes1no0),
	    "Sensuous, Romantic, Sexy": (["a1_mood_Sensuous, Romantic, Sexy"], yes1no0),
	    "Stimulated, Lively, Excited ": (["a1_mood_Stimulated, Lively, Excited "], yes1no0),
	    "Tense, Anxious, Stressed": (["a1_mood_Tense, Anxious, Stressed"], yes1no0),
    },
    'published_date': {
        "_date": (["Year", "Test Quarter"], todate),
    },
    "physical" : {	
	    "Calm": (["Q3__6__When_I_need_to_calm_myself_down_"], yes1no0),
	    "Cleanse Body": (["Q3__8__When_I_need_to_cleanse_my_body_and_mind_"], yes1no0),
	    "Comments": (["Q3__10__Others__please_specify_COMMENTS"], yes1no0),
	    "Cool": (["Q3__4__When_I_need_to_cool_myself_down_"], yes1no0),
	    "Energize": (["Q3__5__When_I_need_to_energize_myself_"], yes1no0),
	    "Hydronate": (["Q3__1__When_I_need_to_hydrate_myself_"], yes1no0),
	    "Others": (["Q3__10__Others__please_specify"], yes1no0),
	    "Quench": (["Q3__2__When_I_need_to_quench_my_thirst__"], yes1no0),
	    "Refresh Breath": (["Q3__9__When_I_need_to_refresh_my_breath_"], yes1no0),
	    "Restore Body": (["Q3__7__When_I_need_to_restore_my_body_and_mind_"], yes1no0),
	    "Statisfy Hunger": (["Q3__3__When_I_need_to_satisfy_my_hunger_"], yes1no0),
    },
    "suitable_product" : {	
	    "Liquid Detergent": (["Is this a smell you would like to have in a_Liquid Detergent"], yes1no0),
	    "Powder Detergent": (["Is this a smell you would like to have in a_Powder Detergent"], yes1no0),
	    "Laundry bars": (["Is this a smell you would like to have in a_Laundry bars (ASIA LATAM AFRICA)/Unit dose (EAME)"], yes1no0),
	    "Softener ": (["Is this a smell you would like to have in a_Softener "], yes1no0),
	    "Scent boosters": (["Is this a smell you would like to have in a_Scent boosters"], yes1no0),
	    "None": (["Is this a smell you would like to have in a_None"], yes1no0),
    },	
    "suitable_stage" : {	
	    "Open": (["When open the pack"], yes1no0),
	    "Closing": (["While dosing"], yes1no0),
	    "Doing the laundry": (["While doing the laundry"], yes1no0),
	    "Wet laundry ": (["On wet laundry coming out of the machine"], yes1no0),
	    "Wet clothes drying line": (["When hanging wet clothes on the line/when drying"], yes1no0),
	    "Removing clothes line": (["When removing clothes from the line/dryer"], yes1no0),
	    "Clothes in the closet": (["My clothes in the closet"], yes1no0),
	    "Ironing": (["While ironing"], yes1no0),
	    "Wearing first time": (["When wearing clothes for the first time"], yes1no0),
	    "Wearing at the end day": (["At the end of the day wearing my clothes "], yes1no0),
	    "When using towels": (["When using towels"], yes1no0),
	    "On bed": (["On bed using bed sheets"], yes1no0),
	    "None": (["None"], yes1no0),
    },    	    	    	
}

aggr2ans = {
    "Liking"        : ["liking.keyword"],
    }

qst2fld = {
    "affective"         : (["affective"], 'nested_qst_ans'),
    "ballot"            : (["ballot"], 'nested_qst_ans'),
    "behavioral"        : (["behavioral"], 'nested_qst_ans'),
    "children"          : (["children"], 'nested_qst_ans'),
    "concept"           : (["concept"], 'nested_qst_ans'),
    "descriptors"       : (["descriptors"], 'nested_qst_ans'),
    "descriptors1"      : (["descriptors1"], 'nested_qst_ans'),
    "descriptors2"      : (["descriptors2"], 'nested_qst_ans'),
    "descriptors3"      : (["descriptors3"], 'nested_qst_ans'),
    "descriptors4"      : (["descriptors4"], 'nested_qst_ans'),
    "emotion"           : (["emotion"], 'nested_qst_ans'),
    "fit_descriptors1"  : (["fit_descriptors1"], 'nested_qst_ans'),
    "fragrattr"         : (["fragrattr"], 'nested_qst_ans'),
    "hedonics"          : (["hedonics"], 'nested_qst_ans'),
    "liking"            : (["liking"], 'text'),
    "mood"              : (["mood"], 'nested_qst_ans'),
    "physical"          : (["physical"], 'nested_qst_ans'),
    "smell"             : (["smell"], 'nested_qst_ans'),
    "suitable_product"  : (["suitable_product"], 'nested_qst_ans'),
    "suitable_stage"    : (["suitable_stage"], 'nested_qst_ans'),
    "attributes"        : (["attributes"], 'nested_qst_ans'),
    "platform"          : (["platform"], 'nested_qst_ans'),
    "color"             : (["color"], 'nested_qst_ans'),
    "newness"           : (["newness"], 'nested_qst_ans'),
    "consumer_nature"   : (["consumer_nature"], 'nested_qst_ans'),
    "expected_benefits" : (["expected_benefits"], 'nested_qst_ans'),
    "health_condition"  : (["health_condition"], 'nested_qst_ans'),
    "ideal_benefits"    : (["ideal_benefits"], 'nested_qst_ans'),
    "industry"          : (["industry"], 'nested_qst_ans'),
    "format_rejected"   : (["format_rejected"], 'nested_qst_ans'),
    "format_used"       : (["format_used"], 'nested_qst_ans'),
    "product"           : (["product"], 'nested_qst_ans'),
    "published_date"    : (["published_date"], 'date'),
    "purpose"           : (["purpose"], 'nested_qst_ans'),
    "olfactive_attr"    : (["olfactive_attr"], 'nested_qst_ans'),
    }

surveys = {
    "fresh and clean" : {
        "header"    : ["survey", "category"],
        "_id"       : ["resp_id", "blindcode"],
        'questions' : [
                    "concept",
                    "emotion",
                    "mood",
                    "liking",
                    "suitable_product",
                    "suitable_stage",
                    ],
        },
    "orange beverages" : {
        "header"    : ["survey", "category"],
        "_id"       : ["resp_id", "blindcode"],
        'questions' : [
                    "hedonics",
                    "affective",
                    "ballot",
                    "descriptors",
                    "behavioral",
                    "liking",
                    "physical",
                    ],
        },
    "global panels" : {
        "header"    : ["survey", "published_date", "category"],
        "_id"       : ["resp_id", "blindcode"],
        'questions' : [ # question in sequence of Questionnaire for mapping
                    "industry",
                    "health_condition",
                    "liking",
                    "hedonics",
                    "attributes",
                    "platform",
                    "expected_benefits",
                    "ideal_benefits",
                    "olfactive_attr",
                    "color",
                    "newness",
                    "consumer_nature",
                    "format_rejected",
                    "format_used",
                    "product",
                    'published_date',
                    "purpose",
                    ],
        'screener_q': [
                # (Qx, Question Descr, Question)
                ("Q1", "Gender", "gender"),
                ("Q2", "Age", "age"),
                ("Q3", "Work in Industry", "industry"),
                ("Q4", "Health Condition", "health_condition")
                ],
        'prod_eval_q': [
                # (Qx, Question Descr, Question)
                ("Q1", "Fragrance Liking", "liking"),
                ("Q2", "Intensity JAR", "hedonics"),
                ("Q3", "Attributes", "attributes"),
                ("Q4", "Main Benefits", "platform"),
                ("Q5", "Personal Wash Multicode", "expected_benefits"),
                ("Q5a", "Personal Wash Multicode", "ideal_benefits"),
                ("Q6", "Olfative Attributes", "olfactive_attr"),
                ("Q7", "Colors", "color"),
                ("Q8", "Newness", "newness"),
            ]
        },
    "invictus ul" : {
        "header"    : ["survey", "category"],
        "_id"       : ["resp_id", "blindcode"],
        'questions' : [ # question in sequence of Questionnaire for mapping
                    "descriptors1",
                    "descriptors2",
                    "descriptors3",
                    "color",
                    "descriptors4",
                    "fit_descriptors1",
                    "liking",
                    ],
        'screener_q': [
                # (Qx, Question Descr, Question)
                ("Q1", "Group", "group_id"),
                ("Q2", "Age", "age"),
                ],
        'prod_eval_q': [
                # (Qx, Question Descr, Question)
                ("Q1A", "Descriptor 1", "descriptors1"),
                ("Q1B", "Descriptor 2", "descriptors2"),
                ("Q1C", "Descriptor 3", "descriptors3"),
                ("Q2", "Colors", "color"),
                ("Q3A", "Main territory board", ""),
                ("Q3B", "Sub territory board", ""),
                ("Q4", "Descriptor 4", "descriptors4"),
                ("Q2", "Intensity JAR", "hedonics"),
                ("Q3", "Attributes", "attributes"),
                ("Q4", "Descriptor 4", "descriptors4"),
                ("Q5", "Fit Descriptor 1", "fit_descriptors1"),
                ("Q6", "Liking", "liking"),
                ("Q6", "Intensity", "intensity"),
            ]
        },
    }


# mapping_file = 'Panel_QAs.json'
def qa_map(map_filename):
    global qa
    with open('data/'+ map_filename) as panel_raw_data:
        panel_columns = json.load(panel_raw_data)

    ci_qa_temp = {}

    for i in range(len(panel_columns)):
        ci_qa_temp.update(panel_columns[i])

    for i in ci_qa_temp:
        qa[i] = {}
        for j in ci_qa_temp[i]:
            qa[i][j] = ([ci_qa_temp[i][j][0]], eval(ci_qa_temp[i][j][1]))
    return qa

def answer_value_to_string(answer_value):
    if type(answer_value) == int:
        answer_value = "{0:d}".format(answer_value)
    elif type(answer_value) == float:
        answer_value = "{0:.2f}".format(answer_value)
    elif type(answer_value) == str:
        answer_value = answer_value.strip()
    return answer_value


def answer_value_encode(question, answer, field, answer_value):
    global qa

    answer_code = answer_value
    if question == None:
        if field in fld_encode:
            for code, values in fld_encode[field].items():
                if answer_value in values:
                    answer_code = code
                    return answer_code
    if question in qa:
        if answer in qa[question]:
            encoder = qa[question][answer][1]
            answer_code = encoder(answer_value)
    return answer_code

def answer_values_dict(answer_values, keys):
    field_value = {}
    for ix in range(0, len(keys)):
        if ix < len(answer_values):
            answer_value = answer_values[ix]
        else:
            answer_value = ""
        field_value[keys[ix]] = answer_value
    return field_value
 
def answer_value_decode(answer, answer_code):
    global qa

    answer_value = answer_code
    if type(answer_code) == str:
        first_code = answer_code.split()[0]
        if first_code.isdigit():
            answer_value = int(float(first_code))
    return answer_value
       
def seekerview_answer_value_decode(seererview, answer, answer_code):
    return answer_value_decode(answer, answer_code)


def col_map_field(column):
    global col2fld

    for field, field_map in col2fld.items():
        columns = field_map[0]
        field_type = field_map[1]
        if len(field_map) > 2:
            field_attrs = field_map[2]
        else:
            field_attrs = None
        if column.strip() in columns:
            return field, field_type, field_attrs
    return None, None, None


def aggr_map_ans(aggr):
    global aggr2ans

    for answer, aggrs in aggr2ans.items():
        if aggr in aggrs:
            return answer
    return None

def qst_map_field(question):
    global qst2fld

    for field, field_map in qst2fld.items():
        questions = field_map[0]
        field_type = field_map[1]
        if len(field_map) > 2:
            field_attrs = field_map[2]
        else:
            field_attrs = None
        if question in questions:
            return field, field_type, field_attrs
    return None, None, None

def col_map_answer(survey_name, column, col_map):
    # col_map[column] = (field, question, answer, field_type
    global surveys
    # trun excel column into a qa_column, no trailing spaces and unique suffix, the .1 extension in case of a duplicate header column
    qa_column = column.strip().split('.')[0]

    questions = surveys[survey_name]['questions']
    for question in questions:
        answers = qa[question]
        for answer, map in answers.items():
            columns = map[0]
            if qa_column in columns:
                # test whether column already mapped, if so search for a 2nd mapping
                found = False
                for col_name in col_map.keys():
                    qa_col_name = col_name.strip().split('.')[0]
                    if qa_column == qa_col_name:
                        found = True
                        break
                if not found:
                    return question, answer
                else:
                    if col_map[col_name][1] != question:
                        return question, answer
    return None, None


def map_column(survey_name, column, col_map):
    # returns ES fieldname, question and nested ES fieldname (=answer)
    # Check on a direct mapping between column and field
    field, field_type, field_attrs = col_map_field(column)
    if field:
        col_map[column] = (field, None, None, field_type, field_attrs)
        return field, None, None, field_type, field_attrs
    # Check on a mapping to an answer
    question, answer = col_map_answer(survey_name, column, col_map)
    if answer:
        # Check wheter answer belongs to a question
        if question:
            # Check on a mapping between question and field
            field, field_type, field_attrs = qst_map_field(question)
            col_map[column] = (field, question, answer, field_type)
            return field, question, answer, field_type, field_attrs
    col_map[column] = (None, None, None, None, None)
    return None, None, None, None, None


def map_columns(survey_name, columns):
    field_map = {}
    col_map = {}
    for column in columns:
        field, question, answer, field_type, field_attrs = map_column(survey_name, column, col_map)
        col_map[column] = (field, question, answer, field_type)
        if field != None:
            if field not in field_map.keys():
                field_map[field] = [(question, answer, column, field_type, field_attrs)]
            else:
                field_map[field].append((question, answer, column, field_type, field_attrs))
    # make sure the header and _id fields are mapped. If not, they have to be entered
    header_map = {}
    for field in surveys[survey_name]['header']:
        if field in field_map.keys():
            header_map[field] = (field_map[field], None)
        else:
            if field == 'survey':
                options = [survey_name]
            if field == 'category':
                options = [{"cat":"Personal Wash"}, {"cat":"Home Care"}, {"cat":"Fabric Care"}, {"cat":"Hair Care"}, {"cat":"Toiletries"}, {"cat":"Fine Fragr"}, {"cat":"Flavors"}]
            header_map[field] = (None, options)
    for field in surveys[survey_name]['_id']:
        if field in field_map.keys():
            header_map[field] = (field_map[field], None)
        else:
            header_map[field] = (None, ["option2"])
    return field_map, col_map, header_map

def map_header(request, survey_name, data):
    global surveys

    for field in surveys[survey_name]['header']:
        if field not in data:
            variable_name = field + '_hdr'
            if variable_name in request.POST:
                field_value = request.POST[variable_name]
                field_value = field_value.replace("'", '"')
                try:
                    field_value = json.loads(field_value) # in case of category
                except:
                    field_value = request.POST[variable_name]
                data[field] = field_value
    pass

def map_id(survey_name, data):
    global surveys

    id = ""
    for field in surveys[survey_name]['_id']:
        if field in data:
            if len(id) > 0:
                id = id + "_"
            id  = id + data[field]
    return id



