import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / 'data'
DATA_DIR.mkdir(exist_ok=True)
AUDIO_DIR = DATA_DIR / 'audio'
AUDIO_DIR.mkdir(exist_ok=True)

commands = [
    (1, 'hi', 'मेरी बेकरी "श्री स्वाद" है, हम केक, पेस्ट्री और ब्रेड बनाते हैं, 20% छूट है, लाल और सुनहरा रंग पसंद है', 'instagram_post', 'bakery', 'red,gold', 'opening', 'स्वाद, विश्वास और ताज़गी', 'केक,पेस्ट्री,ब्रेड', '9876543210', 'A bakery shop opening poster with red and gold accents and premium food photography.'),
    (2, 'mr', 'माझी दुकान "श्री नटरंग" आहे, आम्ही साड्या, लेहेंगा आणि जुने ड्रेस बनवतो, नवीन दुकान उद्घाटन, गुलाबी व सोन्याचा रंग', 'instagram_post', 'saree shop', 'pink,gold', 'opening', 'शोभायमान शैली', 'साड्या,लेहेंगा,ड्रेस', '9876543210', 'A saree boutique opening design in pink and gold with Indian ethnic elegance.'),
    (3, 'hi', 'यह "शिवा टेलर" है, कपड़े बदलते हैं,Alteration और custom stitching, सुबह 9 से रात 9 तक', 'instagram_post', 'tailor shop', 'blue,black', 'service', 'परफेक्ट फिट, हर बार', 'सिलाई,अल्टरेशन,कस्टम', '9123456789', 'A tailor shop ad showing precise fitting, custom stitching, and modern service hours.'),
    (4, 'mr', 'आमची चाय दुकान "गर्वीण चहा" आहे, चहा, समोसा आणि केक देतो, 10% सवलत, निळा आणि पिवळा रंग', 'instagram_post', 'chai stall', 'blue,yellow', 'discount', 'ताज्या चहाचे आकर्षण', 'चहा,समोसा,केक', '9988776655', 'A chai stall poster with hot snacks, a discount offer, and warm street-food atmosphere.'),
    (5, 'hi', 'ये "दीपक मिठाई" है, हम जलेबी, लड्डू और रसगुल्ले बनाते हैं, दिवाली ऑफर, लाल और सुनहरा रंग', 'festival_post', 'sweet shop', 'red,gold', 'festival', 'दीपावली का मधुर आनंद', 'जलेबी,लड्डू,रसगुल्ले', '9900112233', 'A festive sweets shop promotional poster with Diwali colors and premium desserts.'),
    (6, 'mr', 'माझी बुटिक "सूर्यकिरण" आहे, मेकअप, हेअर स्पा आणि फेशियल करतो, 30% ऑफर, गुलाबी व सफेद रंग', 'beauty salon', 'pink,white', 'offer', 'सुंदरता का नया आयाम', 'मेकअप,हेयरस्पा,फेशियल', '9999887766', 'A beauty salon poster featuring bridal glam, facial and hair spa services, and a 30% offer.'),
    (7, 'hi', 'हमारा मोबाइल रिपेयर शॉप "किरण टेक" है, 500 रुपये तक छूट, फोन रिपेयर और एक्सेसरीज़', 'instagram_post', 'mobile shop', 'blue,cyan', 'discount', 'ताज़ा टेक्नोलॉजी', 'रिपेयर,एक्सेसरी,फोन', '9001122334', 'A mobile repair shop graphic with phone accessories and technician service discount.'),
    (8, 'mr', 'आमची दुकान "वनस्पती वेध" आहे, योग क्लास, मेडिटेशन आणि आयुर्वेदिक सत्र, हिरवा आणि निळा रंग', 'instagram_post', 'yoga studio', 'green,blue', 'wellness', 'आरोग्याची सुरुवात', 'योग,मेडिटेशन,सत्र', '9988774400', 'A yoga studio poster with wellness classes and calming green-blue tones.'),
    (9, 'hi', 'श्रीकृष्ण बुटिक में saree, lehenga और bridal wear है, शादी के सीज़न में 25% ऑफर', 'instagram_post', 'saree shop', 'purple,cream', 'wedding', 'परिवार का सुंदर सपना', 'साड़ी,लेहेंगा,ब्राइडल', '9887766554', 'A bridal fashion boutique poster for wedding collections with premium ethnic styling.'),
    (10, 'mr', 'आमची किराणा दुकान "भुवन अन्न" आहे, ताजे भाजी, धान्य आणि मसाले, दरवाजापासून सेवा', 'instagram_post', 'grocery', 'green,orange', 'daily', 'ताजेसे आणि विश्वासार्ह', 'भाजी,धान्य,मसाले', '9777665544', 'A grocery shop poster showing fresh vegetables, grains, and daily essentials.'),
    (11, 'hi', '"गोल्डन स्पर्श" ज्वेलरी स्टोर है, सोने की चूड़ी, नेकलेस और कंगन, 15% ऑफर', 'instagram_post', 'jewelry', 'gold,black', 'festival', 'चमकदार रूप', 'चूड़ी,नेकल्स,कंगन', '9811223344', 'A jewelry store poster with gold ornaments and festive offer styling.'),
    (12, 'mr', 'आमच्या दुकानात "शुभकामना" टेलर सेवा आहे, पॅन्ट, शर्ट आणि साडी फिटिंग, आजच बुक करा', 'instagram_post', 'tailor shop', 'navy,white', 'booking', 'सगळी फिटिंगमध्ये निपुणता', 'पॅन्ट,शर्ट,साडी', '9880011223', 'A tailor shop poster for shirt, pant, and saree fitting with a booking CTA.'),
    (13, 'hi', 'रा. अंबे पार्क में "हरियाली चौक" कॉफी शॉप है, कॉफी, समोसा और पेस्ट्री, सुबह 8 से रात 10', 'instagram_post', 'cafe', 'brown,cream', 'daily', 'ताज़ा स्वाद, हर बार', 'कॉफी,समोसा,पेस्ट्री', '9822334455', 'A cafe poster featuring coffee, snacks, and evening ambience with storefront branding.'),
    (14, 'mr', 'माझ्या दुकानाचे नाव "ताज खरेदी" आहे, कपडे, ज्वेलरी आणि हँडबैग, नवे स्टॉक उपलब्ध', 'instagram_post', 'shop', 'purple,black', 'new stock', 'नवीन शैली, सर्वकाळ', 'कपडे,ज्वेलरी,हँडबैग', '8855667788', 'A general store poster with new arrivals and mixed-category products.'),
    (15, 'hi', 'कामधेनु बेकरी, केक, कुकीज और पुकेट्स, 10% ऑफर, डेजर्ट लवर्स के लिए', 'instagram_post', 'bakery', 'cream,brown', 'offer', 'ताज़ा और स्वादिष्ट', 'केक,कुकीज,पुकेट्स', '9866554433', 'A bakery design for desserts and cookies with a special discount and warm tones.'),
    (16, 'mr', 'आमची "नवजीवन ट्रॅक" जिम आहे, फिटनेस ट्रेनिंग, वजन कमीकरण आणि योग, 25% सवलत', 'instagram_post', 'gym', 'red,black', 'offer', 'शक्ती आणि समतोल', 'फिटनेस,योग,क्लास', '9766554433', 'A gym poster highlighting transformation, training, and a strong offer.'),
    (17, 'hi', '"राधा फ्लॉवर शॉप" में गुलाब, गुलदस्ता और शादी के फूल उपलब्ध हैं, आज ही ऑर्डर करें', 'instagram_post', 'flowers', 'pink,green', 'occasion', 'हर पल में रंग', 'गुलाब,गुलदस्ता,फूल', '9811227766', 'A flower shop poster featuring floral bouquets and event orders with soft pastel colors.'),
    (18, 'mr', 'आमची दुकान "आकाश इलेक्ट्रॉनिक्स" आहे, लैपटॉप, प्रिंटर आणि गरजेनुसार सेवा, नवे मॉडल उपलब्ध', 'instagram_post', 'electronics', 'blue,black', 'new model', 'तंत्रज्ञानाचा आनंद', 'लॅपटॉप,प्रिंटर,सेवा', '9090909090', 'An electronics store ad for laptops, printers, and support with modern blue styling.'),
    (19, 'hi', 'ये "सुरभि ब्यूटी पार्लर" है, bridal makeup, hair spa और facial, 35% ऑफर', 'instagram_post', 'beauty salon', 'pink,gold', 'wedding', 'प्रत्येक बनावट में सुंदरता', 'ब्राइडल,हेयरस्पा,फेशियल', '9898989898', 'A beauty salon wedding poster showcasing bridal makeup and beauty services.'),
    (20, 'mr', 'माझी "स्वाती ज्वेलरी" दुकान आहे, मंगळसूत्र, नथ, आणि कंगणे, दिवाळी विशेष', 'festival_post', 'jewelry', 'gold,red', 'festival', 'सोन्याची चमक', 'मंगळसूत्र,नथ,कंगणे', '9877123456', 'A festive jewelry shop poster with ornaments, gifting, and Diwali colors.'),
    (21, 'hi', '"सुखद चाय" कपड़ों के साथ कचहरी नहीं, नमी रहित, हम रेहड़ी पर चाय दी जाती है', 'instagram_post', 'chai stall', 'orange,red', 'daily', 'हर कप में ताज़गी', 'चाय,समोसा,सैंडविच', '9258741369', 'A vibrant chai stall poster with tea, samosa, and a warm street-cart feel.'),
    (22, 'mr', 'आमची दुकान "श्याम ट्रेंड्स" आहे, घरगुती कपडे, बेडशिट आणि टॉवल, नवे स्टॉक', 'instagram_post', 'home textiles', 'mustard,cream', 'new stock', 'कुटुंबासाठी सौंदर्य', 'कपडे,बेडशिट,टॉवल', '9823456781', 'A home-textiles shop poster highlighting bedding, towels, and soft home-style décor.'),
    (23, 'hi', 'हमारा "सूरज मेडिकल" क्लिनिक है, डॉक्टर परामर्श, टेस्टिंग और फिजियोथेरपी, नए रोगियों के लिए छूट', 'instagram_post', 'clinic', 'teal,white', 'offer', 'स्वास्थ्य का भरोसा', 'कंसल्टेशन,टेस्ट,फिजियो', '9786543210', 'A medical clinic poster advertising consultation and therapy with clean healthcare colors.'),
    (24, 'mr', 'आमची "गौरव फर्निचर" दुकान आहे, सोफा, टेबल आणि बेड, फर्निचरचे नवे कोर्स', 'instagram_post', 'furniture', 'brown,beige', 'new arrival', 'घराला सुंदर बनवू', 'सोफा,टेबल,बेड', '9944556677', 'A furniture showroom prompt with new styles and practical home décor.'),
    (25, 'hi', 'ये "अमोल बेकरी" है, लंच स्पेशल, तंदूरी rolls औरcakes, ऑर्डर 2pm तक', 'instagram_post', 'bakery', 'orange,cream', 'service', 'अमूल स्वाद, हर दिन', 'रोल्स,केक,स्पेशल', '9899556677', 'A bakery lunch special advertisement with warm bakery colours and quick delivery cues.'),
    (26, 'mr', 'आमच्या होम डेको दुकान "दीपक स्टाइल" आहे, लाइट्स, कुसारी आणि शोपीस, 20% ऑफर', 'instagram_post', 'decor', 'gold,ivory', 'offer', 'घर सुंदर आणि उजळ', 'लाइट्स,कुसारी,शोपीस', '9323456789', 'A home decor store poster with lights and décor pieces and a 20% sale offer.'),
    (27, 'hi', '"पंखुडी ब्यूटी" में bridal makeup, party makeup और nail art है, open today', 'instagram_post', 'beauty salon', 'pink,purple', 'event', 'सबसे सुंदर पल', 'मेकअप,नेलआर्ट,पार्टी', '9812345678', 'A beauty salon poster for bridal and event makeup with a modern glamorous look.'),
    (28, 'mr', 'आमची दुकान "कणिका कटाई" आहे, सिलाई, लेहेंगा एडजस्टमेंट आणि ड्रेपिंग, 12% सवलत', 'instagram_post', 'tailor shop', 'maroon,cream', 'discount', 'तंतोतंत फिट', 'सिलाई,एडजस्टमेंट,ड्रेपिंग', '9312345678', 'A tailor shop poster for adjustments and draping with an elegant maroon palette.'),
    (29, 'hi', 'यह "नवनीत फ्लोर" ग्रोसेरी है, अनाज, दाल, और ताज़ा फल, घर पर डिलीवरी', 'instagram_post', 'grocery', 'green,white', 'delivery', 'हर रसोई का भरोसा', 'अनाज,दाल,फल', '9900990099', 'A grocery store ad with fresh produce and home delivery service.'),
    (30, 'mr', 'आमच्या "सुवास चहा" दुकानात कॉफी, चहा आणि पेस्ट्री सर्व उपलब्ध आहे, खुला रोज', 'instagram_post', 'chai stall', 'brown,cream', 'daily', 'संतुलित स्वाद', 'कॉफी,चहा,पेस्ट्री', '9321122334', 'A café-style chai shop poster with prime snacks and warm ambiance.'),
    (31, 'hi', '"संगम इलेक्ट्रॉनिक्स" में earphones, smartwatches और chargers हैं, नए arrivals', 'instagram_post', 'electronics', 'blue,white', 'new arrival', 'कनेक्टेड जीवन', 'एयरफोन,स्मार्टवॉच,चार्जर', '9311223344', 'An electronics display with accessories and smart devices in a modern setup.'),
    (32, 'mr', 'आमची "मधुर मिठाई" दुकान आहे, पावभाजी, शेक, आणि काकडी केक, फेस्टिव्ह ऑफर', 'festival_post', 'sweet shop', 'yellow,red', 'festival', 'सुखद क्षण', 'पावभाजी,शेक,केक', '9788776655', 'A sweet shop festive banner with desserts and celebratory colors.'),
    (33, 'hi', '"बिंदु योग केंद्र" योग कक्षा, प्राणायाम और ध्यान, 7 दिन का ट्रायल', 'instagram_post', 'yoga studio', 'green,white', 'trial', 'शांत मन का आधार', 'योग,प्राणायाम,ध्यान', '9654321987', 'A yoga studio ad with calm colors, meditative classes, and a 7-day trial.'),
    (34, 'mr', 'आमची दुकान "कुशल टेलर" आहे, स्पोर्ट्स वेअर, कुर्ता आणि ड्रेस मेकिंग, फास्ट डिलिव्हरी', 'instagram_post', 'tailor shop', 'black,gray', 'delivery', 'अचूक आणि जलद', 'स्पोर्ट्सवेअर,कुर्ता,ड्रेस', '9966554477', 'A boutique tailoring poster featuring garments and express delivery service.'),
    (35, 'hi', 'श्री लक्ष्मी ज्वेलरी, wedding sets, bangles और earrings, दीवाली में 20% ऑफर', 'festival_post', 'jewelry', 'gold,maroon', 'festival', 'सुवर्णा रौनक', 'वेडिंगसेट,बंगले,ईयरिंग', '9744556611', 'A festive jewelry shop poster with bridal ornaments and gold-red elegance.'),
    (36, 'mr', 'आमची "हृदय बुटिक" दुकान आहे, मुबलक साड्या, lehenga आणि ब्राइडल वियर, नवीन कलेक्शन', 'instagram_post', 'saree shop', 'purple,rose', 'new collection', 'सजावटी जीवन', 'साड़ी,लेहेंगा,ब्राइडल', '9822003344', 'A boutique fashion poster with bridal wear, heirloom styles, and new collections.'),
    (37, 'hi', '"चमन फलों की दुकान" में आम, केला, संतरा और पपीता है, ताज़ा स्टॉक', 'instagram_post', 'fruit shop', 'orange,green', 'fresh', 'ताज़गी की खुशबू', 'आम,केला,संतरा', '9988223344', 'A fruit shop poster with vibrant produce and fresh-stock messaging.'),
    (38, 'mr', 'आमच्या दुकानाचे नाव "अभिराम ग्रॉसरी" आहे, ताजे धान्य, मसाले आणि भाजीपाला, शॉपिंगची सुविधा', 'instagram_post', 'grocery', 'green,red', 'shopping', 'ताजेपणा आणि भरपूर निवड', 'धान्य,मसाले,भाजी', '9876549988', 'A grocery poster emphasizing quality ingredients and daily shopping convenience.'),
    (39, 'hi', 'सूर्यकिरण सैलून में hair cut, beard grooming और spa, रात्रि 8 बजे तक', 'instagram_post', 'beauty salon', 'navy,white', 'service', 'सही लुक, सही समय', 'हेयरकट,ग्रोमिंग,स्पा', '9300123456', 'A salon poster for grooming and beard care with modern service hours.'),
    (40, 'mr', 'आमची "ताज महल ग्रोसेरी" दुकान आहे, ताजे दूध, दही आणि पनीर, आजच ऑर्डर करा', 'instagram_post', 'grocery', 'white,green', 'daily', 'प्रत्येक घरात ताजेपणा', 'दूध,दही,पनीर', '9733445566', 'A dairy and grocery shop ad with fresh household essentials and daily orders.'),
    (41, 'hi', '"नवीन मोबाइल सेंटर" में smart phones, earbuds और cases, 15% ऑफर', 'instagram_post', 'mobile shop', 'blue,white', 'offer', 'अच्छा कनेक्शन', 'स्मार्टफोन,ईयरबड,केस', '9301234567', 'A mobile shop promotional ad for phones, earbuds, and device accessories.'),
    (42, 'mr', 'आमचे "अतुल्य जिम" आहे, ट्रेंडिंग फिटनेस, बॉडी ट्रांसफॉर्मेशन आणि पर्सनल ट्रेनिंग', 'instagram_post', 'gym', 'red,orange', 'transformation', 'शक्ती आणि सहनशीलता', 'ट्रेनिंग,ट्रांसफॉर्मेशन,फिटनेस', '9811002233', 'A gym advertisement with training and performance improvement messaging.'),
    (43, 'hi', '"ताज महल बेकरी" में wedding cakes, cupcakes और pastries, कस्टम आर्डर', 'instagram_post', 'bakery', 'pink,cream', 'wedding', 'सिर्फ़ खास अवसरों के लिए', 'वेडिंगकेक,कपकेक,पेस्ट्री', '9866778899', 'A bakery wedding special ad for custom cakes and pastries.'),
    (44, 'mr', 'आमची दुकान "प्रेम फ्लोर" आहे, फ्रेश फ्लॉवर, बोक्सेट्स आणि बॅनर डेकोर, आजच ऑर्डर', 'instagram_post', 'flowers', 'rose,white', 'occasion', 'प्रेमाची अभिव्यक्ति', 'फूल,बोक्सेट,डेकोर', '9866557744', 'A flower shop poster with bouquets and event arrangements in soft rose colors.'),
    (45, 'hi', 'मेरा नाम "पुष्पा हार्डवेयर" है, टूल्स, पेंच और घर सुधार सामग्री, भरोसेमंद स्टॉक', 'instagram_post', 'hardware', 'orange,black', 'stock', 'हर घर की जरूरत', 'टूल्स,पेंच,सामग्री', '9887766443', 'A hardware shop ad for tools and home improvement supplies in practical tones.'),
    (46, 'mr', 'आमची "सुगंध पेपर स्टोर" दुकान आहे, कागद, स्टेशनरी आणि ऑफ़िस सामान, नवीन कलेक्शन', 'instagram_post', 'stationery', 'blue,green', 'new collection', 'साफ ग्राफिक्स आणि सुंदर लेखन', 'पेपर,स्टेशनरी,ऑफिस', '9423456781', 'A stationery shop poster with office supplies and a modern business-ready design.'),
    (47, 'hi', 'यह "शिवा ड्राईक्लीन" सेवा है, कॉटन वाश, डस्टिंग और कपड़ों की मरम्मत', 'instagram_post', 'laundry', 'blue,white', 'service', 'स्वच्छता और नमी', 'वाश,डस्टिंग,मरम्मत', '9855667788', 'A laundry service ad with fabric care and cleaning services in crisp blue tones.'),
    (48, 'mr', 'आमची दुकान "आनंद आहार" आहे, हेल्थ फूड, स्मूथी आणि नाश्ता, फास्ट हेल्थ', 'instagram_post', 'health food', 'green,orange', 'health', 'स्वास्थ्याची सुरुवात', 'फूड,स्मूथी,नाश्ता', '9988334455', 'A health food café poster highlighting smoothies, healthy meals, and energy boosts.'),
    (49, 'hi', '"श्रीराम कारपेंटर" दुकान है, फर्नीचर मरम्मत, दरवाज़े और किचन फिक्सिंग', 'instagram_post', 'carpenter', 'brown,beige', 'repair', 'हर घर में सुंदरता', 'मरम्मत,दरवाज़े,किचन', '9876541122', 'A carpenter service ad for furniture repair and home fix-ups.'),
    (50, 'mr', 'आमची दुकान "सारंग बुटिक" आहे, ड्रेस, कास्केट आणि नित्याचे कपडे, नवा सत्र', 'instagram_post', 'fashion', 'gold,black', 'season', 'आठवणी आणि शैली', 'ड्रेस,कास्केट,कपडे', '9765432109', 'A fashion boutique poster with seasonal styles and elegant evening wear.'),
]

commands.extend([
    (51, 'hi', 'भाई थोड़ा classy सा बना देना, हमारी चाय वाली दुकान है, नाम मत बिगाड़ना, लाल भी चलेगा और जो सही लगे, शाम का पोस्ट चाहिए', 'instagram_post', 'chai stall', 'red', 'daily', 'needs_human_review', 'चाय,नाश्ता', '', ''),
    (52, 'mr', 'माझ्या दुकानासाठी एक insta पोस्ट हवी आहे, थोडं modern पण traditional, साड्या आहेत आणि नवीन stock आलाय, रंग तू suggest कर', 'instagram_post', 'saree shop', 'needs_human_review', 'new stock', 'needs_human_review', 'साड्या,लेहेंगा', '', ''),
    (53, 'hi', 'logo नहीं, banner जैसा, अरे वो जो बाहर लगाते हैं, मोबाइल repair और accessories दोनों लिखना, blue maybe', 'banner', 'mobile shop', 'blue', 'service', 'needs_human_review', 'रिपेयर,एक्सेसरीज़', '', ''),
    (54, 'mr', 'काहीतरी festive बनवा ना, दिवाळीला मिठाईची ऑफर आहे पण खूप भरगच्च नको, gold red ठीक आहे', 'festival_post', 'sweet shop', 'gold,red', 'festival', 'needs_human_review', 'मिठाई,ऑफर', '', ''),
    (55, 'hi', 'सुबह से बोल रहा हूं price वाला flyer चाहिए, chai twenty, samosa forty और coffee शायद fifty, check कर लेना', 'price_list_flyer', 'chai stall', 'needs_human_review', 'daily', 'needs_human_review', 'चाय,समोसा,कॉफी', '', ''),
    (56, 'mr', 'हेअर spa आणि facial आहे, bridal पण करतो, पोस्ट जरा premium दिसली पाहिजे, pink नाही तर rose shade', 'instagram_post', 'beauty salon', 'pink', 'service', 'needs_human_review', 'हेअर स्पा,फेशियल,ब्राइडल', '', ''),
    (57, 'hi', 'अरे bakery का नाम श्री स्वाद है, cake pastry bread सब है, opening वाला feel चाहिए पर text कम रखना', 'instagram_post', 'bakery', 'needs_human_review', 'opening', 'needs_human_review', 'केक,पेस्ट्री,ब्रेड', '', ''),
    (58, 'mr', 'योगा क्लाससाठी शांत पोस्ट कर, green blue ठेव, पण meditation शब्द चुकू नये आणि number शेवटी टाक', 'instagram_post', 'yoga studio', 'green,blue', 'wellness', 'needs_human_review', 'योग,मेडिटेशन', '', 'needs_human_review'),
    (59, 'hi', 'दुकान grocery है लेकिन थोड़ा premium, fruits grains मसाले, delivery भी बोल देना, no loud colors', 'instagram_post', 'grocery', 'needs_human_review', 'delivery', 'needs_human_review', 'फल,अनाज,मसाले', '', ''),
    (60, 'mr', 'नवीन फर्निचर आला आहे sofa table bed, साधं clean banner चालेल, beige किंवा brown, बाकी तू बघ', 'banner', 'furniture', 'beige,brown', 'new arrival', 'needs_human_review', 'सोफा,टेबल,बेड', '', '')
])

with open(DATA_DIR / 'commands.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['id', 'language', 'command', 'design_type', 'business_type', 'colors', 'occasion', 'tagline', 'services', 'contact', 'english_reference', 'review_status'])
    writer.writerows([*row, 'needs_human_review' if int(row[0]) >= 51 else 'draft'] for row in commands)

price_lists = [
    (1, 'hi', 'चाय 20, कॉफी 40, सैंडविच 80, बिस्कुट 30', json.dumps([['चाय', 20], ['कॉफी', 40], ['सैंडविच', 80], ['बिस्कुट', 30]], ensure_ascii=False)),
    (2, 'mr', 'चहा 25, कॉफी 45, सँडविच 90, बिस्किट 35', json.dumps([['चहा', 25], ['कॉफी', 45], ['सँडविच', 90], ['बिस्किट', 35]], ensure_ascii=False)),
    (3, 'hi', 'फेसियल 499, हेयर स्पा 799, क्लीनअप 299', json.dumps([['फेसियल', 499], ['हेयर स्पा', 799], ['क्लीनअप', 299]], ensure_ascii=False)),
    (4, 'mr', 'फेशियल 499, हेयर स्पा 799, क्लीनअप 299', json.dumps([['फेशियल', 499], ['हेयर स्पा', 799], ['क्लीनअप', 299]], ensure_ascii=False)),
    (5, 'hi', 'पेठा 120, लड्डू 180, काजू बर्फी 220', json.dumps([['पेठा', 120], ['लड्डू', 180], ['काजू बर्फी', 220]], ensure_ascii=False)),
    (6, 'mr', 'पेठा 120, लड्डू 180, काजू बर्फी 220', json.dumps([['पेठा', 120], ['लड्डू', 180], ['काजू बर्फी', 220]], ensure_ascii=False)),
    (7, 'hi', 'साड़ी 1500, लेहेंगा 2400, ब्लाउज 800', json.dumps([['साड़ी', 1500], ['लेहेंगा', 2400], ['ब्लाउज', 800]], ensure_ascii=False)),
    (8, 'mr', 'साडी 1500, लेहेंगा 2400, ब्लाउज 800', json.dumps([['साडी', 1500], ['लेहेंगा', 2400], ['ब्लाउज', 800]], ensure_ascii=False)),
    (9, 'hi', 'सुबह चाय 20, दोपहर थाली 120, रात नाश्ता 60', json.dumps([['सुबह चाय', 20], ['दोपहर थाली', 120], ['रात नाश्ता', 60]], ensure_ascii=False)),
    (10, 'mr', 'सकाळचा चहा 20, दुपारचा थाली 120, रात्रीचे नाश्ता 60', json.dumps([['सकाळचा चहा', 20], ['दुपारचा थाली', 120], ['रात्रीचे नाश्ता', 60]], ensure_ascii=False)),
    (11, 'hi', 'मेडिकली जांच 450, कंसल्टेशन 300, फिजियो 600', json.dumps([['मेडिकली जांच', 450], ['कंसल्टेशन', 300], ['फिजियो', 600]], ensure_ascii=False)),
    (12, 'mr', 'मेडिकल टेस्ट 450, कन्सल्टेशन 300, फिजियो 600', json.dumps([['मेडिकल टेस्ट', 450], ['कन्सल्टेशन', 300], ['फिजियो', 600]], ensure_ascii=False)),
    (13, 'hi', 'कुंजी 150, पेंडेंट 450, ब्रेसलेट 650', json.dumps([['कुंजी', 150], ['पेंडेंट', 450], ['ब्रेसलेट', 650]], ensure_ascii=False)),
    (14, 'mr', 'कुंजी 150, पेंडेंट 450, ब्रेसलेट 650', json.dumps([['कुंजी', 150], ['पेंडेंट', 450], ['ब्रेसलेट', 650]], ensure_ascii=False)),
    (15, 'hi', 'डोनेशन प्लान 1200, बिना फीस 500, ट्रेवल पैकेज 3500', json.dumps([['डोनेशन प्लान', 1200], ['बिना फीस', 500], ['ट्रेवल पैकेज', 3500]], ensure_ascii=False)),
    (16, 'mr', 'डोनेशन प्लान 1200, फी नाही 500, ट्रेवल पॅकेज 3500', json.dumps([['डोनेशन प्लान', 1200], ['फी नाही', 500], ['ट्रेवल पॅकेज', 3500]], ensure_ascii=False)),
    (17, 'hi', 'कैशबुक 220, पेन 80, नोटबुक 120', json.dumps([['कैशबुक', 220], ['पेन', 80], ['नोटबुक', 120]], ensure_ascii=False)),
    (18, 'mr', 'कॅशबुक 220, पेन 80, नोटबुक 120', json.dumps([['कॅशबुक', 220], ['पेन', 80], ['नोटबुक', 120]], ensure_ascii=False)),
    (19, 'hi', 'मसाला चाय 30, समोसा 40, पकोड़ा 50', json.dumps([['मसाला चाय', 30], ['समोसा', 40], ['पकोड़ा', 50]], ensure_ascii=False)),
    (20, 'mr', 'मसाला चहा 30, समोसा 40, पकोड़ा 50', json.dumps([['मसाला चहा', 30], ['समोसा', 40], ['पकोड़ा', 50]], ensure_ascii=False)),
    (21, 'hi', 'मोबाइल केस 299, चार्जर 399, एयरपड्स 1799', json.dumps([['मोबाइल केस', 299], ['चार्जर', 399], ['एयरपड्स', 1799]], ensure_ascii=False)),
    (22, 'mr', 'मोबाइल केस 299, चार्जर 399, एअरपड्स 1799', json.dumps([['मोबाइल केस', 299], ['चार्जर', 399], ['एअरपड्स', 1799]], ensure_ascii=False)),
    (23, 'hi', 'गुलाब 100, कमल 120, बेला 80', json.dumps([['गुलाब', 100], ['कमल', 120], ['बेला', 80]], ensure_ascii=False)),
    (24, 'mr', 'गुलाब 100, कमळ 120, बेला 80', json.dumps([['गुलाब', 100], ['कमळ', 120], ['बेला', 80]], ensure_ascii=False)),
    (25, 'hi', 'बेसिक फी 500, प्रोफेशनल फी 900, हेयर स्पा 1200', json.dumps([['बेसिक फी', 500], ['प्रोफेशनल फी', 900], ['हेयर स्पा', 1200]], ensure_ascii=False)),
    (26, 'mr', 'बेसिक फेशियल 500, प्रोफेशनल फेशियल 900, हेयर स्पा 1200', json.dumps([['बेसिक फेशियल', 500], ['प्रोफेशनल फेशियल', 900], ['हेयर स्पा', 1200]], ensure_ascii=False)),
    (27, 'hi', 'कटलेट 60, फ्रेंच फ्राइज 80, चिकन रोल 90', json.dumps([['कटलेट', 60], ['फ्रेंच फ्राइज', 80], ['चिकन रोल', 90]], ensure_ascii=False)),
    (28, 'mr', 'कटलेट 60, फ्रेंच फ्राइझ 80, चिकन रोल 90', json.dumps([['कटलेट', 60], ['फ्रेंच फ्राइझ', 80], ['चिकन रोल', 90]], ensure_ascii=False)),
    (29, 'hi', 'दूध 40, दही 45, पनीर 90', json.dumps([['दूध', 40], ['दही', 45], ['पनीर', 90]], ensure_ascii=False)),
    (30, 'mr', 'दूध 40, दही 45, पनिर 90', json.dumps([['दूध', 40], ['दही', 45], ['पनिर', 90]], ensure_ascii=False)),
]

price_lists.extend([
    (31, 'hi', 'चाय बीस रुपये, coffee forty rs और sandwich पचास से सत्तर', json.dumps([['चाय', 20], ['coffee', 40], ['sandwich', [50, 70]]], ensure_ascii=False)),
    (32, 'mr', 'पन्नास रुपये चहा, कॉफी Rs 60, वडा 40 रुपये', json.dumps([['चहा', 50], ['कॉफी', 60], ['वडा', 40]], ensure_ascii=False)),
    (33, 'hi', 'cake - one hundred, pastry दो सौ, bread 50 रुपये', json.dumps([['cake', 100], ['pastry', 200], ['bread', 50]], ensure_ascii=False)),
    (34, 'mr', 'फेशियलची किंमत 499, हेअर स्पा 799 रुपये आणि क्लीनअप rs 299', json.dumps([['फेशियल', 499], ['हेअर स्पा', 799], ['क्लीनअप', 299]], ensure_ascii=False)),
    (35, 'hi', 'साड़ी की price 1500 है; blouse आठ सौ और lehenga 2400', json.dumps([['साड़ी', 1500], ['blouse', 800], ['lehenga', 2400]], ensure_ascii=False)),
    (36, 'mr', 'दूध forty, दही पन्नास, पनीर रुपये 120', json.dumps([['दूध', 40], ['दही', 50], ['पनीर', 120]], ensure_ascii=False)),
    (37, 'hi', 'काजू बर्फी की कीमत ₹220 और लड्डू 180 रुपये', json.dumps([['काजू बर्फी', 220], ['लड्डू', 180]], ensure_ascii=False)),
    (38, 'mr', 'चहा 20 ते 30 रुपये, कॉफी 50', json.dumps([['चहा', [20, 30]], ['कॉफी', 50]], ensure_ascii=False)),
    (39, 'hi', 'starting at 99 rs: notebooks, pen 20 और files तीस', json.dumps([['notebooks', 99], ['pen', 20], ['files', 30]], ensure_ascii=False)),
    (40, 'mr', 'साडी पंधराशे, लेहेंगा दोन हजार चारशे, ब्लाउज आठशे', json.dumps([['साडी', 1500], ['लेहेंगा', 2400], ['ब्लाउज', 800]], ensure_ascii=False)),
    (41, 'hi', 'फेसियल 499 only, hair spa at 799, cleanup for 299', json.dumps([['फेसियल', 499], ['hair spa', 799], ['cleanup', 299]], ensure_ascii=False)),
    (42, 'mr', 'वडा आधी 40, समोसा 30 रुपये, चहा फक्त 20', json.dumps([['वडा', 40], ['समोसा', 30], ['चहा', 20]], ensure_ascii=False)),
    (43, 'hi', 'मोबाइल case रुपये 299, charger is 399 rs, earbuds 1,799', json.dumps([['मोबाइल case', 299], ['charger', 399], ['earbuds', 1799]], ensure_ascii=False)),
    (44, 'mr', 'फुलांचा bouquet 300 ते 500, गुलाब 100 रुपये', json.dumps([['फुलांचा bouquet', [300, 500]], ['गुलाब', 100]], ensure_ascii=False)),
    (45, 'hi', 'consultation: तीन सौ रुपये, test 450, physio छह सौ', json.dumps([['consultation', 300], ['test', 450], ['physio', 600]], ensure_ascii=False))
])

with open(DATA_DIR / 'price_lists.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['id', 'language', 'text', 'gold_pairs_json', 'review_status'])
    writer.writerows([*row, 'needs_human_review' if int(row[0]) >= 31 else 'draft'] for row in price_lists)

with open(DATA_DIR / 'transcripts.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['id', 'audio_file', 'language', 'speaker', 'reference_transcript', 'key_terms'])
    writer.writerow(['1', '', 'hi', 'speaker_1', 'मेरी बेकरी श्री स्वाद है केक पेस्ट्री और ब्रेड', 'बेकरी,केक,ब्रेड'])
    writer.writerow(['2', '', 'mr', 'speaker_2', 'माझी दुकान श्री नटरंग आहे साड्या आणि लेहेंगा', 'दुकान,साड्या,लेहेंगा'])
    writer.writerow(['3', '', 'hi', 'speaker_3', 'यह शिवा टेलर है कपड़े बदलते हैं', 'टेलर,सिलाई,कपड़े'])

print('Prepared experiments data files in', DATA_DIR)
