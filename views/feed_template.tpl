<html>
<head>
<title>{{feed.title}}</title>
<h2><a href={{feed.link}}>{{feed.title}}</a></h2>
</head>
<body>
    <ul>
%for i,entrie in enumerate(feed.entries):
    %entrie_link = '/'.join(["/entries", feed.id_, str(i)])
    %if entrie.has_read:
    <li style="background-color: Gainsboro; color: Gainsboro; margin-bottom: 10px"><a href={{entrie_link}}>{{entrie.title}}</a></li>
    %else:
    <li style="color: LawnGreen; margin-bottom: 10px"><a href={{entrie_link}}>{{entrie.title}}</a></li>
    %end
%end
    </ul>
</body>
</html>
