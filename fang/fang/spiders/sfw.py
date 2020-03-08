# -*- coding: utf-8 -*-
import scrapy
import re
from ..items import NewHouseItem,ESFHouseItem


class SfwSpider(scrapy.Spider):
    name = 'sfw'
    allowed_domains = ['fang.com']
    start_urls = ['https://www.fang.com/SoufunFamily.htm']

    def parse(self, response):
        trs=response.xpath("//div[@class='outCont']//tr")
        province=None
        for tr in trs:
            tds=tr.xpath(".//td[not(@class)]")
            province_td=tds[0]
            province_text=province_td.xpath(".//text()").get()
            province_text=re.sub(r"\s","",province_text)
            if province_text:
                province=province_text
            if province=='其它':
                continue
            city_td=tds[1]
            city_links=city_td.xpath(".//a")
            for city_link in city_links:
                city=city_link.xpath(".//text()").get()
                city_url=city_link.xpath(".//@href").get()

                # print("province",province)
                # print("city:",city)
                # print("url",city_url)
                #url for newhouse
                url_moudule=city_url.split(".")
                newhouse_url=url_moudule[0]+"."+"newhouse."+url_moudule[1]+"."+url_moudule[2]+"house/s/"
                #url for esf
                esf_url=url_moudule[0]+"."+"esf."+url_moudule[1]+"."+url_moudule[2]
                # print('city:',province,city)
                # print(newhouse_url)
                # print(esf_url)
                #yield scrapy.Request(url=newhouse_url,callback=self.parse_newhouse,meta={"info":(province,city)})
                yield scrapy.Request(url=esf_url,callback=self.parse_esf,meta={"info":(province,city)})

    def parse_newhouse(self,response):
        province,city=response.meta.get('info')
        lis=response.xpath("//div[contains(@class,'nl_con')]/ul/li")

        for li in lis:

            names=li.xpath(".//div[@class='nlcd_name']/a/text()").get()
            if names is None:
                continue

            name=names.strip()


            house_type_list=li.xpath(".//div[contains(@class,'house_type')]/a/text()").getall()
            house_type_list=list(map(lambda x:re.sub(r"\s","",x),house_type_list))
            rooms=list(filter(lambda x:x.endswith("居"),house_type_list))

            area="".join(li.xpath(".//div[contains(@class,'house_type')]/text()").getall())
            area=re.sub(r"\s|-|/|－","",area)
            address=li.xpath(".//div[@class='address']/a/@title").get()

            district_text="".join(li.xpath(".//div[@class='address']/a//text()").getall())

            district_text=re.search(r".*\[(.+)\].*",district_text)
            if district_text is None:
                continue

            district=district_text.group(1)
            print(district)

            sale=li.xpath(".//div[contains(@class,'fangyuan')]/span/text()").get()
            price="".join(li.xpath(".//div[@class='nhouse_price']//text()").getall())
            price=re.sub(r"\s|广告","",price)
            origin_url=li.xpath(".//div[@class='nlcd_name']/a/@href").get()
            #print(origin_url)
            item=NewHouseItem(name=name,rooms=rooms,area=area,address=address,district=district,
                            sale=sale,price=price,origin_url=origin_url,province=province,
                         city=city)
            yield item
            next_url=response.xpath(".//div[@class='page']//a[@class='next']/@href").get()
            if next_url:
                yield scrapy.Request(url=response.urljoin(next_url),callback=self.parse_newhouse(),meta={"info":{province,city}})




    def parse_esf(self,response):
        province, city = response.meta.get('info')
        dls=response.xpath("//div[@class='shop_list shop_list_4']/dl")
        for dl in dls:
            item=ESFHouseItem(province=province,city=city)
            item['name']=dl.xpath(".//p[@class='add_shop']/a/@title").get()
            infos=dl.xpath(".//p[@class='tel_shop']/text()").getall()
            infos=list(map(lambda x:re.sub(r"\s","",x),infos))
            for info in infos:
                if "厅" in info:
                    item['rooms']=info
                elif "层"in info:
                    item['floor']=info
                elif "向"in info:
                    item['toward']=info.replace("年建","")
                elif "㎡"in info:
                    item['area']=info

            item['address']=dl.xpath(".//p[@class='add_shop']/span/text()").get()
            item['price']="".join(dl.xpath(".//dd[contains(@class,'price_right')]/span[1]//text()").getall())
            item['unit']= "".join(dl.xpath(".//dd[contains(@class,'price_right')]/span[2]//text()").getall())
            detail=dl.xpath(".//dt[@class='floatl']/a/@href").get()
            item['origin_url']=response.urljoin(detail)
            yield item
        next_url = response.xpath(".//div[@class='page_al']/p/a/@href").get()
        if next_url:
            yield scrapy.Request(url=response.urljoin(next_url),callback=self.parse_esf,meta={"info":{province,city}})