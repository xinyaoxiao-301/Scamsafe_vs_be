-- Create the notifications table
CREATE TABLE IF NOT EXISTS notifications (
    id SERIAL PRIMARY KEY,
    label VARCHAR(10) NOT NULL,
    message TEXT NOT NULL
);

-- Insert all scam messages
INSERT INTO notifications (label, message) VALUES
('scam', 'WINNER!! As a valued network customer you have been selected to receivea RM900 prize reward! To claim call 09061701461. Claim code KL341. Valid 12 hours only.'),
('scam', 'FreeMsg Hey there darling it''s been 3 week''s now and no word back! I''d like some fun you up for it still? Tb ok! XxX std chgs to send, RM1.50 to rcv'),
('scam', 'XXXMobileMovieClub: To use your credit, click the WAP link in the next txt message or click here>> http://wap. xxxmobilemovieclub.com?n=QJKGIGHJJGCBL'),
('scam', 'Are you unique enough? Find out on www.areyouunique.com.my'),
('scam', 'U have a secret admirer who is looking 2 make contact with U-find out who they R*reveal who thinks UR so special-call on 09058094597'),
('scam', '100 dating service cal;l 09064012103 box334sk38ch'),
('scam', 'We know someone who you know that fancies you. Call 09058097218 to find out who. POBox 6, MY 50000 50sen'),
('scam', 'CDs 4u: Congratulations ur awarded RM500 of gift vouchers or RM125 gift guaranteed & Freeentry 2 RM100 wkly draw xt MUSIC to 87066 TnCs www.ldew.com1win150ppmx3age16'),
('scam', 'FREE2DAY sexy Malaysia Day pic of Jordan!Txt PIC to 89080 dont miss out, then every wk a saucy celeb!4 more pics c PocketBabe.com.my 0870241182716 RM3/wk'),
('scam', 'Customer Loyalty Offer:The new iphone for FREE at TXTAUCTION! Txt word: START to No: 81151 & get yours Now! 4T&Ctxt TC 50sen/MTmsg'),
('scam', 'WINNER!! As a valued network customer you have been selected to receivea RM900 prize reward! To claim call 09061701461. Claim code KL341. Valid 12 hours only.'),
('scam', 'URGENT! We are trying to contact you. Last weekends draw shows that you have won a RM900 prize GUARANTEED. Call 09061701939. Claim code S89. Valid 12hrs only'),
('scam', 'Please call our customer service representative on FREEPHONE 0808 145 4742 between 9am-11pm as you have WON a guaranteed RM1000 cash or RM5000 prize!'),
('scam', 'URGENT! We are trying to contact U. Todays draw shows that you have won a RM800 prize GUARANTEED. Call 09050001808 from land line. Claim M95. Valid12hrs only'),
('scam', 'WINNER! As a valued network customer you hvae been selected to receive a RM900 reward! To collect call 09061701444. Valid 24 hours only. ACL03530150PM'),
('scam', 'URGENT We are trying to contact you Last weekends draw shows u have won a RM1000 prize GUARANTEED Call 09064017295 Claim code K52 Valid 12hrs 150p pm'),
('scam', 'URGENT! You have won a 1 week FREE membership in our RM100,000 Prize Jackpot! Txt the word: CLAIM to No: 81010 T&C www.dbuk.net LCCLTD POBOX 4403LDNW1A7RW18'),
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