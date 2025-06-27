
@app.tool("search_web")
async def search_web(
    query: str, 
    scrape_results: bool = DEFAULT_SCRAPE_RESULTS, 
    max_scraped_pages: int = DEFAULT_MAX_SCRAPED_PAGES
) -> List[types.TextContent]:
    """
    Search the web for current information using Google, with optional content scraping.
    
    Use this tool to find recent information, facts, news, or research on any topic.
    Optionally scrape the full content from the top search results for deeper analysis.
    
    Args:
        query: Search terms to find information (e.g., "current weather Tokyo", "Python tutorials")
        scrape_results: Whether to scrape full content from search results (default: True)
        max_scraped_pages: Maximum number of search results to scrape (default: 3, range: 1-10)
    
    Returns:
        List of MCP TextContent objects with search results and optionally scraped content
    """
    logger.debug(f"Executing search_web with query: {query}, scrape_results: {scrape_results}, max_scraped_pages: {max_scraped_pages}")
    
    try:
        # Generate optimized search queries
        query_agent_output = query_agent.run(
            QueryAgentInputSchema(instruction=query, num_queries=DEFAULT_NUM_QUERIES)
        )
        logger.debug(f"Generated queries: {query_agent_output.queries}")
        
        # Validate API credentials
        api_key = os.getenv("GOOGLE_API_KEY")
        cx = os.getenv("GOOGLE_CX")
        if not api_key or not cx:
            error_msg = "Google API credentials not configured"
            logger.error(error_msg)
            return format_bigdata_response(error_msg)
        
        # Execute search
        search_tool = GoogleSearchApiTool(
            config=GoogleSearchApiToolConfig(
                api_key=api_key, cx=cx, max_results=DEFAULT_MAX_RESULTS
            )
        )
        
        search_results = search_tool.run(
            GoogleSearchApiToolInputSchema(queries=query_agent_output.queries)
        )
        
        logger.debug(f"Retrieved {len(search_results.results)} search results")
        
        # Convert search results to the format expected by format_bigdata_response
        formatted_results = []
        for result in search_results.results:
            formatted_results.append({
                "headline": result.title or "No title",
                "url": result.url,
                "content": result.content or "No preview available",
                "scraped": False  # Flag to track scraping status
            })
        
        # If scraping is enabled, scrape the top results
        if scrape_results and formatted_results:
            # Clamp max_scraped_pages to reasonable bounds
            max_scraped_pages = max(1, min(max_scraped_pages, 10, len(formatted_results)))
            
            logger.debug(f"Starting scraping of top {max_scraped_pages} results")
            scraper_tool = WebpageScraperTool()
            
            # Get URLs from top search results
            urls_to_scrape = [result["url"] for result in formatted_results[:max_scraped_pages]]
            
            for i, url in enumerate(urls_to_scrape):
                try:
                    logger.debug(f"Scraping URL {i+1}/{len(urls_to_scrape)}: {url}")
                    
                    scraped_result = await scraper_tool.run(
                        WebpageScraperToolInputSchema(url=url, include_links=True)
                    )
                    
                    if scraped_result.error:
                        logger.warning(f"Failed to scrape {url}: {scraped_result.error}")
                        # Keep original search result content if scraping fails
                        continue
                    else:
                        # Replace with scraped content if successful
                        if scraped_result.content:
                            formatted_results[i]["content"] = scraped_result.content
                            formatted_results[i]["scraped"] = True
                            logger.debug(f"Successfully scraped {url}")
                        
                except Exception as e:
                    logger.error(f"Error scraping {url}: {e}", exc_info=True)
                    # Keep original search result if scraping fails
                    continue
            
            successful_scrapes = len([item for item in formatted_results[:max_scraped_pages] if item.get("scraped")])
            logger.debug(f"Successfully scraped {successful_scrapes} out of {max_scraped_pages} pages")
        
        # Return formatted MCP response
        return format_bigdata_response(formatted_results)
        
    except Exception as e:
        error_msg = f"Error in search_web: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return format_bigdata_response(error_msg)

@app.tool("scrape_urls")
async def scrape_urls(urls: List[str], max_pages: int = 5) -> List[types.TextContent]:
    """
    Scrape content from web pages to get full text content.
    
    Use this tool to extract complete content from specific web pages like articles,
    blog posts, or documentation when you need the full text from known URLs.
    
    Args:
        urls: List of URLs to scrape (e.g., ["https://example.com/article"])
        max_pages: Maximum number of pages to scrape (default: 5, range: 1-10)
    
    Returns:
        List of MCP TextContent objects with scraped content
    """
    logger.debug(f"Executing scrape_urls with {len(urls)} URLs")
    
    try:
        scraper_tool = WebpageScraperTool()
        scraped_content = []
        
        # Clamp max_pages to reasonable bounds
        max_pages = max(1, min(max_pages, 10, len(urls)))
        urls_to_process = urls[:max_pages]
        
        for i, url in enumerate(urls_to_process):
            try:
                logger.debug(f"Scraping URL {i+1}/{len(urls_to_process)}: {url}")
                
                scraped_result = await scraper_tool.run(
                    WebpageScraperToolInputSchema(url=url, include_links=True)
                )
                
                if scraped_result.error:
                    logger.warning(f"Failed to scrape {url}: {scraped_result.error}")
                    # Still add failed attempts to maintain consistency
                    scraped_content.append({
                        "headline": f"Failed to scrape: {url}",
                        "url": url,
                        "content": f"Error: {scraped_result.error}",
                        "scraped": False
                    })
                else:
                    scraped_content.append({
                        "headline": f"Content from {url}",
                        "url": url,
                        "content": scraped_result.content or "No content available",
                        "scraped": True
                    })
            except Exception as e:
                logger.error(f"Error scraping {url}: {e}", exc_info=True)
                scraped_content.append({
                    "headline": f"Failed to scrape: {url}",
                    "url": url,
                    "content": f"Error: {str(e)}",
                    "scraped": False
                })
        
        successful = [item for item in scraped_content if item.get("scraped", False)]
        logger.debug(
            f"Successfully scraped {len(successful)} out of {len(urls_to_process)} pages"
        )
        
        # Return formatted MCP response
        return format_bigdata_response(scraped_content)
        
    except Exception as e:
        error_msg = f"Error in scrape_urls: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return format_bigdata_response(error_msg)