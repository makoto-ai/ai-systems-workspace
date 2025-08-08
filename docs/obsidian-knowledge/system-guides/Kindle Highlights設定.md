## インストール


設定 => コミュニティプラグイン => 閲覧をクリック

Kindle Highlightと入力して、インストール

![[Kindle Highlight設定-1746073056365.webp|473x251]]


有効化 => オプションをクリック

以下のように、設定

![[Kindle Highlight設定-1746073132112.webp|646x204]]



Templates => Manageをクリック


Fine nameにて

- Reset to default templateをクリック
- 📚{{title}} と入力
- 右下のSave 


![[Kindle Highlight設定-1746073585720.webp|517x412]]




File contentにて

- Reset to default templateをクリック
- 元のやつを削除し、こちらをコピーして、貼り付ける
```
# {{title}}

{% trim %}
{% if imageUrl %}![image|150]({{imageUrl}}){% endif %}
{% if author %}**Author**:: [[{{author}}]]{% endif %}
{% if url %}**Source**:: {{url}}{% endif %}
{% endtrim %}

---

## Highlights

{{highlights}}
```

- 右下のSave

![[Kindle Highlight設定-1746073703989.webp|660x538]]



Highlightにて

- Reset to default templateをクリック
- 元のやつを削除し、こちらをコピーして、貼り付ける
```
>{{ text }}
{% if note %}>>[!note]
>{{note}}{% endif %}
---
```

- 右下のSave

![[Kindle Highlight設定-1746074676446.webp|553x451]]


これで設定は、おしまいです！


左のサイドバーの
![[Kindle Highlight設定-1746074733479.webp]]

こちらをクリック、

もしくは、command + P => Kindleと入力し、Sync Highlightsを選択し、同期してください。


02_Configs/ImportedBooks の配下に、

読んだKindle本が、自動で飛んでくれば、成功です！

![[Kindle Highlight設定-1746074795862.webp|313x435]]
