-- Create the notifications table
CREATE TABLE IF NOT EXISTS notifications (
    id SERIAL PRIMARY KEY,
    label VARCHAR(10) NOT NULL,
    message TEXT NOT NULL
);

-- Create the explanation table (3 explanations per notification row)
CREATE TABLE IF NOT EXISTS explanation (
    id SERIAL PRIMARY KEY,
    notification_id INTEGER NOT NULL REFERENCES notifications(id) ON DELETE CASCADE,
    explanation_number SMALLINT NOT NULL CHECK (explanation_number BETWEEN 1 AND 3),
    explanation_text TEXT NOT NULL,
    UNIQUE (notification_id, explanation_number)
);

-- Insert all scam messages
INSERT INTO notifications (label, message) VALUES
('scam', 'WINNER!! As a valued network customer you have been selected to receivea RM900 prize reward! To claim call 09061701461. Claim code KL341. Valid 12 hours only.'),
('scam', 'FreeMsg Hey there darling it''s been 3 week''s now and no word back! I''d like some fun you up for it still? Tb ok! XxX std chgs to send, RM1.50 to rcv'),
('scam', 'XXXMobileMovieClub: To use your credit, click the WAP link in the next txt message or click here>> http://wap. [xxxmobilemovieclub.com](http://xxxmobilemovieclub.com)?n=QJKGIGHJJGCBL'),
('scam', 'Are you unique enough? Find out on [www.areyouunique.com.my](http://www.areyouunique.com.my)'),
('scam', 'U have a secret admirer who is looking 2 make contact with U-find out who they R*reveal who thinks UR so special-call on 09058094597'),
('scam', '100 dating service cal;l 09064012103 box334sk38ch'),
('scam', 'We know someone who you know that fancies you. Call 09058097218 to find out who. POBox 6, MY 50000 50sen'),
('scam', 'CDs 4u: Congratulations ur awarded RM500 of gift vouchers or RM125 gift guaranteed & Freeentry 2 RM100 wkly draw xt MUSIC to 87066 TnCs www.ldew.com1win150ppmx3age16'),
('scam', 'FREE2DAY sexy Malaysia Day pic of Jordan!Txt PIC to 89080 dont miss out, then every wk a saucy celeb!4 more pics c [PocketBabe.com.my](http://PocketBabe.com.my) 0870241182716 RM3/wk'),
('scam', 'Customer Loyalty Offer:The new iphone for FREE at TXTAUCTION! Txt word: START to No: 81151 & get yours Now! 4T&Ctxt TC 50sen/MTmsg'),
('scam', 'WINNER!! As a valued network customer you have been selected to receivea RM900 prize reward! To claim call 09061701461. Claim code KL341. Valid 12 hours only.'),
('scam', 'URGENT! We are trying to contact you. Last weekends draw shows that you have won a RM900 prize GUARANTEED. Call 09061701939. Claim code S89. Valid 12hrs only'),
('scam', 'Please call our customer service representative on FREEPHONE 0808 145 4742 between 9am-11pm as you have WON a guaranteed RM1000 cash or RM5000 prize!'),
('scam', 'URGENT! We are trying to contact U. Todays draw shows that you have won a RM800 prize GUARANTEED. Call 09050001808 from land line. Claim M95. Valid12hrs only'),
('scam', 'WINNER! As a valued network customer you hvae been selected to receive a RM900 reward! To collect call 09061701444. Valid 24 hours only. ACL03530150PM'),
('scam', 'URGENT We are trying to contact you Last weekends draw shows u have won a RM1000 prize GUARANTEED Call 09064017295 Claim code K52 Valid 12hrs 150p pm'),
('scam', 'URGENT! You have won a 1 week FREE membership in our RM100,000 Prize Jackpot! Txt the word: CLAIM to No: 81010 T&C [www.dbuk.net](http://www.dbuk.net) LCCLTD POBOX 4403LDNW1A7RW18'),
('scam', 'As a valued customer, I am pleased to advise you that following recent review of your Mob No. you are awarded with a RM1500 Bonus Prize, call 09066364589'),
('scam', 'Please call our customer service representative on 0800 169 6031 between 10am-9pm as you have WON a guaranteed RM1000 cash or RM5000 prize!'),
('scam', 'We are trying to contact you. Last weekends draw shows that you won a RM1000 prize GUARANTEED. Call 09064012160. Claim Code K52. Valid 12hrs only. 150ppm'),
('scam', 'Congratulations ur awarded 500 Medical vouchers! Only on www.Ldew.com1win150ppmx3age16'),
('scam', 'URGENT!: Your Mobile No. was awarded a RM2,000 Bonus Caller Prize on 02/02/26! This is our 2nd attempt to contact YOU! Call 0871-872-9755 BOX95QU');

-- Insert all not_scam messages
INSERT INTO notifications (label, message) VALUES
('not_scam', 'Save 20% on senior essentials at HealthPlus Clinic this weekend. Bring this SMS in store. T&Cs apply.'),
('not_scam', 'Kejani Cleaning Services offers comprehensive, reliable cleaning solutions. Their expert team provides routine cleaning, deep cleaning, move-in/out cleaning, post-construction cleaning & more, using top-quality equipment & eco-friendly products. Flexible scheduling & competitive pricing available. Contact them today for a spotless home or office! STOP *456*9*5#'),
('not_scam', 'The AEON sale is on! Crazy deals everyday up to 50% just a click away on the AEON Wallet app and FREE delivery all month long! Download today https://play.google.com/store/apps/details?id=today.wander.acs&pli=1'),
('not_scam', 'Keep up with Unifi! Visit https://unifi.com.my to read our latest newsletter, "Owning The Home".'),
('not_scam', 'Get clientele HELP Cover today. Debi check and we will cover your premium this December. Yes =call. No=out. AUTHFSP. T&C bit.ly/tc.CL.NO.=OptOut'),
('not_scam', 'Get 2.5GB + 100 Telkom Mins +2 Bob/ Min to other networks for RM 99 valid for 30 days. Dial *544*1*3# NOW!'),
('not_scam', 'Enjoy more talktime when you recharge your HotLink line! Using your bank account, you get 5% bonus on every Airtime recharge you do. To activate, login to the Hotlink app.'),
('not_scam', 'Ride & save with 5% off 5 Grab rides up to RM100 off valid for a limited time. Use code GRAB25'),
('not_scam', 'RAILWAY FURNISHERS*Don''t Laybuy It - Railway IT! Open your 24 month account and get your goods upon approval. NO interest! Visit a branch TODAY! STOP2OPTOUT'),
('not_scam', 'With 24-hour concierge service, free Wi-Fi, and convenient airport access, Sunway Sanctuary blends healthcare, hospitality, and wellness.'),
('not_scam', 'Amazing DATA deals on your Pulse Plan today! Dial *406*2# to enjoy 1.5GB DATA at N500 to browse your favorite websites.'),
('not_scam', 'Did you know that saving on CIMB increases your chances of qualifying for a loan limit? Start now on https://www.cimb.com.my/en/personal/home.html'),
('not_scam', 'SMILE DENTAL CLINIC: Senior discount – 20% OFF dentures & dental check-ups in May. Our gentle team ensures your comfort. Call 03-6250 7788 or WhatsApp us to book. Mention SMS SENIOR at counter.');

-- Insert explanations for scam messages (notification_id 1–22)
INSERT INTO explanation (notification_id, explanation_number, explanation_text) VALUES

-- id 1: WINNER!! RM900 prize reward
(1, 1, 'It falsely claims the recipient has been specially selected to win a large cash prize, a hallmark tactic of lottery scam messages.'),
(1, 2, 'It pressures the recipient to call a premium-rate number quickly by imposing a fabricated 12-hour deadline.'),
(1, 3, 'No legitimate prize draw contacts winners by unsolicited SMS demanding they call a number to claim a reward.'),

-- id 2: FreeMsg Hey there darling
(2, 1, 'It uses fabricated romantic familiarity with a stranger to lure them into replying, which triggers hidden premium-rate SMS charges.'),
(2, 2, 'The message deliberately buries the fee disclosure ("std chgs", "RM1.50 to rcv") in small abbreviated text to deceive the recipient.'),
(2, 3, 'Legitimate personal messages do not include automated charge notices, making the commercial intent clear despite the personal tone.'),

-- id 3: XXXMobileMovieClub
(3, 1, 'It refers to undisclosed "credit" to manipulate recipients into clicking an unsolicited WAP link that likely enrolls them in a paid subscription.'),
(3, 2, 'The obfuscated URL format is a classic phishing technique used to disguise the true destination of a link.'),
(3, 3, 'The adult-content branding combined with a vague "credit" hook is a well-documented mobile billing fraud pattern.'),

-- id 4: Are you unique enough
(4, 1, 'It uses psychological curiosity bait ("are you unique enough?") to trick recipients into visiting an unknown website that may harvest personal data.'),
(4, 2, 'The message provides no sender identity, no opt-out mechanism, and no explanation of what the site actually does.'),
(4, 3, 'Unsolicited SMS messages promoting anonymous third-party websites with no business context are a common vector for phishing and data theft.'),

-- id 5: U have a secret admirer
(5, 1, 'It exploits human curiosity about romantic interest to pressure the recipient into calling a premium-rate number that charges per minute.'),
(5, 2, 'The "secret admirer" premise is entirely fabricated and cannot be fulfilled; it exists solely to generate call revenue.'),
(5, 3, 'No legitimate matchmaking or social service reveals personal information through unsolicited premium-rate SMS calls.'),

-- id 6: 100 dating service
(6, 1, 'It advertises a vague "dating service" through an unsolicited message with only a premium-rate phone number and no verifiable business identity.'),
(6, 2, 'The garbled formatting ("cal;l", "box334sk38ch") is typical of auto-generated bulk scam messages designed to evade spam filters.'),
(6, 3, 'Legitimate dating platforms use registered apps or websites, not cryptic cold SMS messages with no opt-out or legal information.'),

-- id 7: We know someone who fancies you
(7, 1, 'It manufactures a false social scenario about someone "fancying" the recipient to entice them into calling a chargeable number.'),
(7, 2, 'The inclusion of a PO Box address is a tactic to appear more legitimate while concealing the actual operator behind the scam.'),
(7, 3, 'Charging recipients 50 sen per call to learn the identity of a fabricated admirer is a textbook premium-rate SMS fraud.'),

-- id 8: CDs 4u RM500 gift vouchers
(8, 1, 'It falsely claims the recipient has already been "awarded" prizes worth hundreds of ringgit to pressure them into texting a shortcode that incurs charges.'),
(8, 2, 'The terms are buried in a barely readable string of characters ("150ppmx3age16"), deliberately obscuring the true cost and conditions.'),
(8, 3, 'Legitimate retailers do not award prizes by anonymous unsolicited SMS with shortcode actions and hidden per-message fees.'),

-- id 9: FREE2DAY sexy Malaysia Day pic
(9, 1, 'It uses adult-content bait and a "free" offer to lure recipients into texting a shortcode that silently enrolls them in a RM3/week paid subscription.'),
(9, 2, 'The recurring weekly billing is hidden at the very end of the message after the enticing offer, a deceptive dark pattern.'),
(9, 3, 'The unsolicited sexual content combined with a premium shortcode and recurring charge is a classic mobile content subscription scam.'),

-- id 10: Customer Loyalty iphone free
(10, 1, 'It falsely offers a free iPhone through a fictitious "TXTAUCTION" loyalty program to trick recipients into texting a chargeable shortcode.'),
(10, 2, 'No phone carrier or retailer distributes premium smartphones for free via an unsolicited SMS shortcode action.'),
(10, 3, 'The obscured T&C reference ("50sen/MTmsg") reveals per-message charges that only appear after the recipient has already acted on the offer.'),

-- id 11: Duplicate of id 1
(11, 1, 'It falsely notifies the recipient that they have won a RM900 prize, exploiting prize-draw excitement to lure them into calling a premium-rate number.'),
(11, 2, 'The artificial 12-hour urgency window is a pressure tactic designed to prevent the recipient from verifying the legitimacy of the message.'),
(11, 3, 'The "claim code" creates a false sense of personalisation to make a mass-broadcast scam SMS appear targeted to the individual recipient.'),

-- id 12: URGENT RM900 prize guaranteed
(12, 1, 'The all-caps "URGENT" opener is a social engineering tactic to manufacture anxiety and reduce the recipient''s critical thinking.'),
(12, 2, 'Claiming a prize is "GUARANTEED" is a red flag; legitimate lotteries never guarantee winnings and never contact winners by cold SMS.'),
(12, 3, 'The 12-hour validity window discourages the recipient from consulting others or researching the number before calling.'),

-- id 13: FREEPHONE RM1000 cash
(13, 1, 'Labelling a number as "FREEPHONE" while offering a guaranteed RM1000 prize is deceptive, as the number is a premium-rate line not a free helpline.'),
(13, 2, 'The dual prize structure (RM1000 cash or RM5000 prize) creates an illusion of certainty about winning something, which no real contest can offer.'),
(13, 3, 'Legitimate customer service lines do not contact consumers to announce prize winnings via generic mass SMS broadcasts.'),

-- id 14: URGENT RM800 prize land line
(14, 1, 'Instructing the recipient to call from a landline is a tactic to maximise call duration charges billed to the recipient on a premium-rate number.'),
(14, 2, 'The "GUARANTEED" prize claim combined with an urgent deadline is a textbook combination used in advance-fee and premium-rate phone scams.'),
(14, 3, 'A legitimate prize notification would include the contest name, operator details, and a verifiable claim process rather than just a phone number.'),

-- id 15: WINNER RM900 reward 24 hours
(15, 1, 'The deliberate misspelling ("hvae") is characteristic of auto-generated bulk scam messages and suggests the message was never written by a real person.'),
(15, 2, 'Varying the deadline to 24 hours (compared to other near-identical scam variants using 12 hours) shows this is part of a templated fraud campaign.'),
(15, 3, 'The vague alphanumeric code appended at the end ("ACL03530150PM") mimics a transaction reference to add false legitimacy.'),

-- id 16: URGENT RM1000 guaranteed 150p pm
(16, 1, 'The "150p pm" suffix reveals a 150 pence (or paise) per-minute charge that the recipient will incur when they call the premium number.'),
(16, 2, 'The message is nearly identical to several others in the dataset, confirming it originates from a coordinated templated scam operation.'),
(16, 3, 'Calling the recipient "you" without any account detail or name makes it impossible for this to be a personalised, legitimate prize notification.'),

-- id 17: URGENT RM100,000 Prize Jackpot
(17, 1, 'Inflating the prize to RM100,000 is a deliberate escalation tactic to overcome recipient scepticism and compel them to text the shortcode.'),
(17, 2, 'The embedded website and POBOX details are fake legitimacy signals designed to make a mass-SMS scam look like an organised business.'),
(17, 3, 'A genuine RM100,000 jackpot winner would be contacted by registered mail or a direct call from a verifiable legal entity, not an unsolicited SMS.'),

-- id 18: Valued customer RM1500 Bonus Prize
(18, 1, 'The formal opening ("As a valued customer, I am pleased to advise") mimics official business correspondence to lower the recipient''s guard.'),
(18, 2, 'Referencing a "recent review of your Mob No." fabricates a credible reason for the contact while providing no verifiable details.'),
(18, 3, 'Legitimate companies that award bonuses do so through authenticated account portals or written notices, not by sending cold SMS messages with call-to-action phone numbers.'),

-- id 19: 0800 169 6031 RM1000 cash
(19, 1, 'It replicates the format of a genuine customer service message almost exactly, making it especially deceptive for recipients unfamiliar with SMS prize scams.'),
(19, 2, 'Offering a "guaranteed RM1000 cash or RM5000 prize" is logically contradictory for any real contest and signals a fabricated reward.'),
(19, 3, 'The specific business-hours window (10am-9pm) is added to create a veneer of professionalism around what is a fraudulent premium-rate call scheme.'),

-- id 20: Last weekends draw RM1000 150ppm
(20, 1, 'The "150ppm" suffix at the end discloses the per-minute charge only after the recipient has already been urged to call, violating fair disclosure standards.'),
(20, 2, 'The reference to a "last weekend''s draw" the recipient never entered is a fabricated hook designed to make a random cold SMS appear relevant.'),
(20, 3, 'Repeating the word "GUARANTEED" for a prize linked to a draw the recipient has no memory of entering is a clear indicator of fraud.'),

-- id 21: Congratulations RM500 Medical vouchers
(21, 1, 'Framing the prize as "Medical vouchers" exploits healthcare urgency to make recipients more likely to act without scrutiny.'),
(21, 2, 'The URL contains hidden per-message charges ("150ppmx3") that recipients would only discover after visiting the site and incurring costs.'),
(21, 3, 'No genuine healthcare provider distributes medical vouchers through unsolicited SMS competitions linked to third-party gambling-style websites.'),

-- id 22: URGENT RM2,000 Bonus Caller Prize
(22, 1, 'Claiming this is a "2nd attempt to contact" fabricates prior engagement history to make the recipient feel they are at risk of missing out.'),
(22, 2, 'Attaching a specific past date ("02/02/26") to the alleged prize award creates false specificity to make the fabricated story seem credible.'),
(22, 3, 'A "Bonus Caller Prize" awarded to a random mobile number is not a recognised contest format and exists solely to generate premium-rate call revenue.'),

-- Insert explanations for not_scam messages (notification_id 23–35)

-- id 23: HealthPlus 20% senior discount
(23, 1, 'It is a straightforward promotional offer from a named clinic with a clear, verifiable discount and a transparent in-store redemption process.'),
(23, 2, 'It includes a T&Cs reference and requires the recipient to physically present the SMS, indicating a legitimate retail promotion rather than a remote-charge scheme.'),
(23, 3, 'It does not ask the recipient to call a premium number, click an unverified link, or provide personal information to claim the offer.'),

-- id 24: Kejani Cleaning Services
(24, 1, 'It is a business advertisement from a named cleaning company that describes specific, verifiable services without requesting money, personal data, or any immediate action.'),
(24, 2, 'It includes a standard STOP opt-out code, which is a regulatory requirement for legitimate bulk SMS marketing in many jurisdictions.'),
(24, 3, 'The message makes no false prize claims, carries no hidden charges, and promotes only a real service category with transparent pricing language.'),

-- id 25: AEON Wallet app sale
(25, 1, 'It is an official promotional message from AEON, a well-known retail chain, directing recipients to a verifiable Google Play Store listing for their own branded app.'),
(25, 2, 'The link points to the official Google Play Store domain, which is a trusted platform, rather than an obfuscated or third-party URL.'),
(25, 3, 'The offer (50% off and free delivery) is a standard retail sale promotion with no hidden charges, premium numbers, or requests for personal information.'),

-- id 26: Unifi newsletter
(26, 1, 'It is a subscriber update from Unifi, a legitimate Malaysian internet service provider, directing customers to their official website domain.'),
(26, 2, 'The message contains no prize claims, no premium-rate numbers, and no requests for sensitive information — only a link to branded editorial content.'),
(26, 3, 'The unifi.com.my domain is the verified official website of the service provider, making this a routine customer communication rather than a phishing attempt.'),

-- id 27: Clientele HELP Cover
(27, 1, 'It is a financial services marketing SMS that includes an AUTHFSP compliance marker, a T&C link, and a clear opt-out instruction, all of which indicate regulatory adherence.'),
(27, 2, 'The binary response mechanism (Yes/No) is a standard consent-collection format used by licensed insurance and financial services providers.'),
(27, 3, 'It explicitly offers a complimentary premium payment as a genuine incentive, which is a normal promotional tactic for insurance products, not a deceptive charge scheme.'),

-- id 28: Telkom data bundle dial
(28, 1, 'It is a data bundle offer from a telecom provider using a standard USSD dial code (*544*1*3#), which is a verified activation method native to mobile networks.'),
(28, 2, 'The pricing (RM 99 for 30 days) is stated upfront and clearly, with no hidden fees or post-activation charge surprises.'),
(28, 3, 'USSD shortcodes are a transparent, carrier-controlled interaction channel that cannot silently enrol recipients in services without their active input.'),

-- id 29: HotLink Airtime recharge bonus
(29, 1, 'It is a customer loyalty communication from HotLink, a registered Malaysian mobile operator, promoting a bonus tied to the user''s existing line and banking account.'),
(29, 2, 'The activation requires logging into the official Hotlink app, meaning no money or data is taken without the customer''s authenticated consent.'),
(29, 3, 'A 5% airtime bonus on recharges is a standard mobile operator incentive and does not involve any prize claims, premium calls, or undisclosed fees.'),

-- id 30: Grab discount code
(30, 1, 'It is a promotional offer from Grab, a widely used ride-hailing platform, providing a discount promo code that users can independently verify in the official app.'),
(30, 2, 'The offer structure (5% off, up to RM100, limited time, specific code) is transparently formatted and consistent with how legitimate e-commerce promotions are communicated.'),
(30, 3, 'It asks recipients only to use a discount code within the Grab app, requiring no personal data, no premium-rate calls, and no upfront payment.'),

-- id 31: Railway Furnishers account
(31, 1, 'It is a retail credit account advertisement from a named furniture brand that includes a STOP opt-out code, indicating compliance with bulk SMS marketing regulations.'),
(31, 2, 'The offer (24-month account, goods on approval, no interest) describes a verifiable retail financing product, not a fabricated prize or hidden subscription.'),
(31, 3, 'It directs recipients to a physical branch rather than an anonymous phone number or unverified link, which is consistent with a legitimate bricks-and-mortar retailer.'),

-- id 32: Sunway Sanctuary wellness
(32, 1, 'It is an informational brand message from Sunway Sanctuary, a known Malaysian healthcare and hospitality property, describing genuine amenities without requesting any action.'),
(32, 2, 'The message contains no call to action, no phone number to call, no link to click, and no subscription to join, eliminating all typical scam risk vectors.'),
(32, 3, 'Factual descriptions of real, verifiable property services (concierge, Wi-Fi, airport access) are consistent with legitimate hospitality or healthcare marketing communications.'),

-- id 33: Pulse Plan data deal
(33, 1, 'It is a targeted data bundle promotion that uses a USSD dial code for activation, a transparent and carrier-sanctioned method that cannot silently charge the user.'),
(33, 2, 'The price (N500 for 1.5GB) is stated plainly upfront with no hidden recurring fees or misleading terms buried in the message.'),
(33, 3, 'A personalised reference to the recipient''s existing "Pulse Plan" suggests this is sent by the recipient''s own mobile carrier to an active subscriber, not a random cold broadcast.'),

-- id 34: CIMB savings loan tip
(34, 1, 'It is an educational nudge from CIMB, a major Malaysian bank, directing existing customers to their official verified website rather than requesting any sensitive information.'),
(34, 2, 'The cimb.com.my domain is the bank''s official website, so directing recipients there is consistent with normal authenticated customer engagement, not phishing.'),
(34, 3, 'The message only encourages saving behaviour and loan awareness; it makes no prize claims, requests no personal data, and imposes no charges.'),

-- id 35: Smile Dental Clinic senior discount
(35, 1, 'It is a time-limited seasonal promotion from a named dental clinic offering a specific discount on real dental services with a verifiable contact number and WhatsApp option.'),
(35, 2, 'The requirement to "Mention SMS SENIOR at counter" confirms this is an in-person redemption offer, eliminating the remote-charge risk associated with scam messages.'),
(35, 3, 'A registered clinic advertising dental discounts via SMS with a real local phone number is entirely consistent with legitimate small-business healthcare marketing.');