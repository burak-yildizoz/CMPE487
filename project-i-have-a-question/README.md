TODO:

1- Her bir yeni soruda, oyda ve cevapta, aktör diğer kullanıcılara yaptığı değişkliği broadcast olarak gönderecek.
- (Soru için gönderilecek bilgiler: Soruyu yazan kişi (bu zaten her mesajda gönderiliyor), sorunun başlığı, sorunun içeriği)
- (Cevap için gönderilecek bilgiler: İlgili sorunun başlığı, cevap içeriği, yorumu yazan kişi (aynı şekilde her mesaj))
- (Oy için gönderilecek bilgiler, İlgili sorunun başlığı (her halükarda), -1 mi +1 mi, eğer cevap oylanmışsa ilgili cevap veya hashi (soru için hash sıkıntı çünkü çok soru olabilir ama bir soruya cevaplar sınırlı))
* kalan işler: cevap için id gönderme henüz eklenmedi, bu yüzden oy da verilemiyor.

2- Herhangi bi güncelleme de herkes elindeki veriyi güncelleyecek ama bi hata olması durumunda sıkıntı çıkmaması için bir kullanıcı bir soruya girdiğinde sorunun içeriğini hashleyecek ve bunu diğer kullanıcılara atacak (boradcast). Diğer kullanıcılar ellerindeki hashlerle kontrol edecekler ve broadcast yapan kullanıcıya bunu gönderecekler. Broadcast yapan kişi çoğunluktaki hash'i doğru kabul edip kendi hash'i ile karşılaştıracak. Eğer çoğunluktan farklı ise çoğunluktan birinden soruya ait bilgiler istenecek (tcp). Bu bilgiler cevap sayısı, her cevabın hashi ve her cevaba (tabi ki soruya da) verilen toplam mutlak değer oy sayısı. Eğer karşı tarafın cevap sayısı daha fazla ise kendi elinde olmayan hashlerin içeriğini iste. (farklılık durumunda diğer taraf da 2-'yi çağırıp güncellese fena olmaz ama şimdilik boşver, nasıl olsa fark eder :D). Oy sayısı farklı olanda yine mutlak değeri yüksek olan doğrudur.
* kaşan işler: Kontrol mekanizması henüz eklenmedi ancak önlem olarak udp paketleri üçer defa gönderiliyor. 

3- Yeni birisi uygulamaya girdiğinde broadcast atacak, ona cevap gelecek. Yeni giren cevaplardan birisini rastgele seçecek ve bana tüm veriyi gönder diye ona tekrar tcp atacak. O da ona tüm veriyi gönderecek.
* kalan işler: Henüz implement edilmedi.
