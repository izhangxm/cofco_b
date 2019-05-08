# cofco_b

一个爬虫系统，支持ScienceDirect和Pubmed两个网站

禁止商用

### 环境
- python 3
- mysql 5.7
其他依赖见`reqirements.txt`

### 运行
```
python manager.py runserver 0.0.0.0:9001 --noreload
```

### 测试

查看相应的页面即可

### 状态记录
**content 文章表格的状态含义**

1 爬虫爬取成功存入到数据库，也表示处于未审核状态
-1 该文章已删除
-2 该文章在黑名单当中，之后不再重复标注和爬取
-3 爬虫爬取失败

```
MIT License

Copyright (c) 2019 百变魔君 将心独运

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
