<?php $LastBillet = $manager->getLastBillet();
?>



	<!DOCTYPE html>
	<html>

	<head>
		<title>Coffee Break a Blog Category Flat Bootstarp responsive Website Template | Home :: w3layouts</title>
		<meta name="viewport" content="width=device-width, initial-scale=1">
		<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
		<meta name="keywords" content="Coffee Break Responsive web template, Bootstrap Web Templates, Flat Web Templates, Andriod Compatible web template, 
Smartphone Compatible web template, free webdesigns for Nokia, Samsung, LG, SonyErricsson, Motorola web design" />
		<script type="application/x-javascript">
			addEventListener("load", function () {
				setTimeout(hideURLbar, 0);
			}, false);

			function hideURLbar() {
				window.scrollTo(0, 1);
			}
		</script>
		<link href="css/bootstrap.css" rel='stylesheet' type='text/css' />
		<link href="css/style.css" rel='stylesheet' type='text/css' />
		<script src="js/jquery.min.js"></script>
		<!---- start-smoth-scrolling---->
		<script type="text/javascript" src="js/move-top.js"></script>
		<script type="text/javascript" src="js/easing.js"></script>
		<script type="text/javascript">
			jQuery(document).ready(function ($) {
				$(".scroll").click(function (event) {
					event.preventDefault();
					$('html,body').animate({
						scrollTop: $(this.hash).offset().top
					}, 1000);
				});
			});
		</script>
		<!--start-smoth-scrolling-->
	</head>

	<body>
		<!--header-top-starts-->
		<div class="header-top">
			<div class="container">
				<div class="head-main">
					<a href="index.html"><img src="images/logo-1.png" alt="" /></a>
				</div>
			</div>
		</div>
		<!--header-top-end-->
		<!--start-header-->
		<!-- *************include menu *******************-->


		<?php include ( 'menu.php'); ?>

			<!-- *************include menu *******************-->
			<!-- script-for-menu -->
			<!-- script-for-menu -->
			<script>
				$("span.menu").click(function () {
					$(" ul.navig").slideToggle("slow", function () {});
				});
			</script>
			<!-- script-for-menu -->
			<!--banner-starts-->
			<div class="banner">
				<div class="container">
					<div class="banner-top">
						<div class="banner-text">
							<h2>Billet simple pour l'Alaska</h2>
							<h1>Résumé du livre</h1>
							<div class="banner-btn">
								<a href="resume.php">En savoir plus</a>
							</div>
						</div>
					</div>
				</div>
			</div>
			<!--banner-end-->
			<!--about-starts-->
			<div class="about">
				<div class="container">
					<div class="about-main">
						<div class="col-md-8 about-left">
							<div class="about-one">
								<p>Derniers chapitres</p>

								<?php foreach($LastBillet as $billet);?>
									<h3><?php echo $billet->getTitre()?></h3>
							</div>
							<div class="about-two">
								<a href="single.php?billet_id=<?php echo $billet->getId();?>"><img src="<?php echo $billet->getImage()?>" alt="<?php echo $billet->getAlt()?> " /></a>
								<p>Posté par <a href="about.php"><?php echo $billet->getAuteur()?></a> Le
									<?php echo $billet->getDateCreation()?> <a href="#">comments(2)</a></p>
								<p>
									<?php echo $billet->getContenu()?>
								</p>
								<div class="about-btn">
									<a href="single.php?billet_id=<?php echo $billet->getId();?>">En savoir plus</a>
								</div>
								<ul>
									<li>
										<p>Share : </p>
									</li>
									<li><a href="#"><span class="fb"> </span></a></li>
									<li><a href="#"><span class="twit"> </span></a></li>
									<li><a href="#"><span class="pin"> </span></a></li>
									<li><a href="#"><span class="rss"> </span></a></li>
									<li><a href="#"><span class="drbl"> </span></a></li>
								</ul>
							</div>







							<div class="about-tre">
								<div class="a-1">
									<div class="col-md-6 abt-left">
										<a href="single.html"><img src="images/c-3.jpg" alt="" /></a>
										<h6>Find The Most</h6>
										<h3><a href="single.html">Tasty Coffee</a></h3>
										<p>Vivamus interdum diam diam, non faucibus tortor consequat vitae. Proin sit amet augue sed massa pellentesque viverra. Suspendisse iaculis purus eget est pretium aliquam ut sed diam.</p>
										<label>May 29, 2015</label>
									</div>
									<div class="col-md-6 abt-left">
										<a href="single.html"><img src="images/c-4.jpg" alt="" /></a>
										<h6>Find The Most</h6>
										<h3><a href="single.html">Tasty Coffee</a></h3>
										<p>Vivamus interdum diam diam, non faucibus tortor consequat vitae. Proin sit amet augue sed massa pellentesque viverra. Suspendisse iaculis purus eget est pretium aliquam ut sed diam.</p>
										<label>May 29, 2015</label>
									</div>
									<div class="clearfix"></div>
								</div>
								<div class="a-1">
									<div class="col-md-6 abt-left">
										<a href="single.html"><img src="images/c-5.jpg" alt="" /></a>
										<h6>Find The Most</h6>
										<h3><a href="single.html">Tasty Coffee</a></h3>
										<p>Vivamus interdum diam diam, non faucibus tortor consequat vitae. Proin sit amet augue sed massa pellentesque viverra. Suspendisse iaculis purus eget est pretium aliquam ut sed diam.</p>
										<label>May 29, 2015</label>
									</div>
									<div class="col-md-6 abt-left">
										<a href="single.html"><img src="images/c-6.jpg" alt="" /></a>
										<h6>Find The Most</h6>
										<h3><a href="single.html">Tasty Coffee</a></h3>
										<p>Vivamus interdum diam diam, non faucibus tortor consequat vitae. Proin sit amet augue sed massa pellentesque viverra. Suspendisse iaculis purus eget est pretium aliquam ut sed diam.</p>
										<label>May 29, 2015</label>
									</div>
									<div class="clearfix"></div>
								</div>
								<div class="a-1">
									<div class="col-md-6 abt-left">
										<a href="single.html"><img src="images/c-7.jpg" alt="" /></a>
										<h6>Find The Most</h6>
										<h3><a href="single.html">Tasty Coffee</a></h3>
										<p>Vivamus interdum diam diam, non faucibus tortor consequat vitae. Proin sit amet augue sed massa pellentesque viverra. Suspendisse iaculis purus eget est pretium aliquam ut sed diam.</p>
										<label>May 29, 2015</label>
									</div>
									<div class="col-md-6 abt-left">
										<a href="single.html"><img src="images/c-8.jpg" alt="" /></a>
										<h6>Find The Most</h6>
										<h3><a href="single.html">Tasty Coffee</a></h3>
										<p>Vivamus interdum diam diam, non faucibus tortor consequat vitae. Proin sit amet augue sed massa pellentesque viverra. Suspendisse iaculis purus eget est pretium aliquam ut sed diam.</p>
										<label>May 29, 2015</label>
									</div>
									<div class="clearfix"></div>
								</div>
							</div>
						</div>
						<div class="col-md-4 about-right heading">
							<div class="abt-1">
								<h3>ABOUT US</h3>
								<div class="abt-one">
									<img src="images/c-2.jpg" alt="" />
									<p>Quisque non tellus vitae mauris luctus aliquam sit amet id velit. Mauris ut dapibus nulla, a dictum neque.</p>
									<div class="a-btn">
										<a href="single.html">Read More</a>
									</div>
								</div>
							</div>
							<div class="abt-2">
								<h3>YOU MIGHT ALSO LIKE</h3>
								<div class="might-grid">
									<div class="grid-might">
										<a href="single.html"><img src="images/c-12.jpg" class="img-responsive" alt=""> </a>
									</div>
									<div class="might-top">
										<h4><a href="single.html">Duis consectetur gravida</a></h4>
										<p>Nullam non magna lobortis, faucibus erat eu, consequat justo. Suspendisse commodo nibh odio.</p>
									</div>
									<div class="clearfix"></div>
								</div>
								<div class="might-grid">
									<div class="grid-might">
										<a href="single.html"><img src="images/c-10.jpg" class="img-responsive" alt=""> </a>
									</div>
									<div class="might-top">
										<h4><a href="single.html">Duis consectetur gravida</a></h4>
										<p> Nullam non magna lobortis, faucibus erat eu, consequat justo. Suspendisse commodo nibh odio.</p>
									</div>
									<div class="clearfix"></div>
								</div>
								<div class="might-grid">
									<div class="grid-might">
										<a href="single.html"><img src="images/c-11.jpg" class="img-responsive" alt=""> </a>
									</div>
									<div class="might-top">
										<h4><a href="single.html">Duis consectetur gravida</a></h4>
										<p> Nullam non magna lobortis, faucibus erat eu, consequat justo. Suspendisse commodo nibh odio.</p>
									</div>
									<div class="clearfix"></div>
								</div>
							</div>
							<div class="abt-2">
								<h3>ARCHIVES</h3>
								<ul>
									<li><a href="single.html">Lorem Ipsum is simply dummy text of the printing and typesetting industry. </a></li>
									<li><a href="single.html">Lorem Ipsum has been the industry's standard dummy text ever since the 1500s</a></li>
									<li><a href="single.html">When an unknown printer took a galley of type and scrambled it to make a type specimen book. </a> </li>
									<li><a href="single.html">It has survived not only five centuries, but also the leap into electronic typesetting</a> </li>
									<li><a href="single.html">Remaining essentially unchanged. It was popularised in the 1960s with the release of </a> </li>
									<li><a href="single.html">Letraset sheets containing Lorem Ipsum passages, and more recently with desktop publishing </a> </li>
									<li><a href="single.html">Software like Aldus PageMaker including versionsof Lorem Ipsum.</a> </li>
								</ul>
							</div>
							<div class="abt-2">
								<h3>NEWS LETTER</h3>
								<div class="news">
									<form>
										<input type="text" value="Email" onfocus="this.value = '';" onblur="if (this.value == '') {this.value = 'Email';}" />
										<input type="submit" value="Subscribe">
									</form>
								</div>
							</div>
						</div>
						<div class="clearfix"></div>
					</div>
				</div>
			</div>
			<!--about-end-->
			<!--slide-starts-->
			<div class="slide">
				<div class="container">
					<div class="fle-xsel">
						<ul id="flexiselDemo3">
							<li>
								<a href="#">
									<div class="banner-1">
										<img src="images/s-1.jpg" class="img-responsive" alt="">
									</div>
								</a>
							</li>
							<li>
								<a href="#">
									<div class="banner-1">
										<img src="images/s-2.jpg" class="img-responsive" alt="">
									</div>
								</a>
							</li>
							<li>
								<a href="#">
									<div class="banner-1">
										<img src="images/s-3.jpg" class="img-responsive" alt="">
									</div>
								</a>
							</li>
							<li>
								<a href="#">
									<div class="banner-1">
										<img src="images/s-4.jpg" class="img-responsive" alt="">
									</div>
								</a>
							</li>
							<li>
								<a href="#">
									<div class="banner-1">
										<img src="images/s-5.jpg" class="img-responsive" alt="">
									</div>
								</a>
							</li>
							<li>
								<a href="#">
									<div class="banner-1">
										<img src="images/s-6.jpg" class="img-responsive" alt="">
									</div>
								</a>
							</li>
						</ul>

						<script type="text/javascript">
							$(window).load(function () {

								$("#flexiselDemo3").flexisel({
									visibleItems: 5,
									animationSpeed: 1000,
									autoPlay: true,
									autoPlaySpeed: 3000,
									pauseOnHover: true,
									enableResponsiveBreakpoints: true,
									responsiveBreakpoints: {
										portrait: {
											changePoint: 480,
											visibleItems: 2
										},
										landscape: {
											changePoint: 640,
											visibleItems: 3
										},
										tablet: {
											changePoint: 768,
											visibleItems: 3
										}
									}
								});

							});
						</script>
						<script type="text/javascript" src="js/jquery.flexisel.js"></script>
						<div class="clearfix"> </div>
					</div>
				</div>
			</div>
			<!--slide-end-->
			<!-- *************include footer *******************-->

			<?php include ( 'footer.php'); ?>

				<!-- *************include footer *******************-->

	</body>

	</html>