<?php 
//modele : Acces au donnes

try
{
	$bdd = new PDO('mysql:host=localhost;dbname=projet_blog_p3;charset=utf8', 'root', 'root');
}
catch (Exception $e)
{
        die('Erreur : ' . $e->getMessage());
}

$query = "SELECT * FROM billets ORDER BY date_creation, name";
$req =$bdd->prepare($query);
$req->execute();

// PDO::FETCH_ASSOC = retourne un tableau indexé par le nom de la colonne comme retourné dans le jeu de résultats

while ($row = $req->fetch(PDO::FETCH_ASSOC)) {
	
	$unbillet = array(
		'id'=> $row['id'],
		'image'=> $row['image'],
		'alt'=> $row['alt'],
		'titre'=> $row['titre'],
		'contenu'=> $row['contenu'],
		'auteur'=> $row['auteur'],
		'date_creation'=> $row['date_creation'],
	);
$touslesbillets[]=$unarticle;
	
}

//traitement 



//vue

;?>

	<!DOCTYPE html>
	<html>

	<!-- on récupere le headers  -->
	<?php include_once("header.php"); ?>



		<body>


			<?php include_once("header_top.php"); ?>

				<?php include_once("menu.php"); ?>

					<?php include_once("banner.php"); ?>



						<!--about-starts-->
						<div class="about">
							<div class="container">
								<div class="about-main">
									<div class="col-md-8 about-left">
										<div class="about-one">
											<p>Find The Most</p>
											<h3>Coffee of the month</h3>
										</div>
										<div class="about-two">
											<a href="single.php"><img src="images/c-1.jpg" alt="" /></a>
											<p>Posted by <a href="#">Johnson</a> on 10 feb, 2015 <a href="#">comments(2)</a></p>
											<p>Phasellus fringilla enim nibh, ac pharetra nulla vestibulum ac. Donec tempor fermentum felis, non placerat sem ultrices ut. Nam molestie nunc nec felis hendrerit, in pulvinar arcu mollis. Quisque eget purus nec velit venenatis tincidunt vitae ac massa. Proin vel ornare tellus. Duis consectetur gravida tellus ut varius. Aenean tellus massa, laoreet ut euismod et, pretium id ex. Mauris hendrerit suscipit hendrerit.</p>
											<p>Quisque ultrices ligula a nisl porttitor, vitae porta tortor eleifend. Nulla nec imperdiet ipsum, ut cursus mauris. Proin ut sodales sem, quis vestibulum libero. Proin tempor venenatis congue. Phasellus mollis massa sit amet pharetra consequat. Aliquam quis lacus at sapien tempor semper. Sed ultrices et metus et elementum. Nunc sed justo at erat consequat mollis et eu lectus.</p>
											<div class="about-btn">
												<a href="single.php">Read More</a>
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
													<a href="single.php"><img src="images/c-3.jpg" alt="" /></a>
													<h6>Find The Most</h6>
													<h3><a href="single.php">Tasty Coffee</a></h3>
													<p>Vivamus interdum diam diam, non faucibus tortor consequat vitae. Proin sit amet augue sed massa pellentesque viverra. Suspendisse iaculis purus eget est pretium aliquam ut sed diam.</p>
													<label>May 29, 2015</label>
												</div>
												<div class="col-md-6 abt-left">
													<a href="single.php"><img src="images/c-4.jpg" alt="" /></a>
													<h6>Find The Most</h6>
													<h3><a href="single.php">Tasty Coffee</a></h3>
													<p>Vivamus interdum diam diam, non faucibus tortor consequat vitae. Proin sit amet augue sed massa pellentesque viverra. Suspendisse iaculis purus eget est pretium aliquam ut sed diam.</p>
													<label>May 29, 2015</label>
												</div>
												<div class="clearfix"></div>
											</div>
											<div class="a-1">
												<div class="col-md-6 abt-left">
													<a href="single.php"><img src="images/c-5.jpg" alt="" /></a>
													<h6>Find The Most</h6>
													<h3><a href="single.php">Tasty Coffee</a></h3>
													<p>Vivamus interdum diam diam, non faucibus tortor consequat vitae. Proin sit amet augue sed massa pellentesque viverra. Suspendisse iaculis purus eget est pretium aliquam ut sed diam.</p>
													<label>May 29, 2015</label>
												</div>
												<div class="col-md-6 abt-left">
													<a href="single.php"><img src="images/c-6.jpg" alt="" /></a>
													<h6>Find The Most</h6>
													<h3><a href="single.php">Tasty Coffee</a></h3>
													<p>Vivamus interdum diam diam, non faucibus tortor consequat vitae. Proin sit amet augue sed massa pellentesque viverra. Suspendisse iaculis purus eget est pretium aliquam ut sed diam.</p>
													<label>May 29, 2015</label>
												</div>
												<div class="clearfix"></div>
											</div>
											<div class="a-1">
												<div class="col-md-6 abt-left">
													<a href="single.php"><img src="images/c-7.jpg" alt="" /></a>
													<h6>Find The Most</h6>
													<h3><a href="single.php">Tasty Coffee</a></h3>
													<p>Vivamus interdum diam diam, non faucibus tortor consequat vitae. Proin sit amet augue sed massa pellentesque viverra. Suspendisse iaculis purus eget est pretium aliquam ut sed diam.</p>
													<label>May 29, 2015</label>
												</div>
												<div class="col-md-6 abt-left">
													<a href="single.php"><img src="images/c-8.jpg" alt="" /></a>
													<h6>Find The Most</h6>
													<h3><a href="single.php">Tasty Coffee</a></h3>
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
													<a href="single.php">Read More</a>
												</div>
											</div>
										</div>
										<div class="abt-2">
											<h3>YOU MIGHT ALSO LIKE</h3>
											<div class="might-grid">
												<div class="grid-might">
													<a href="single.php"><img src="images/c-12.jpg" class="img-responsive" alt=""> </a>
												</div>
												<div class="might-top">
													<h4><a href="single.php">Duis consectetur gravida</a></h4>
													<p>Nullam non magna lobortis, faucibus erat eu, consequat justo. Suspendisse commodo nibh odio.</p>
												</div>
												<div class="clearfix"></div>
											</div>
											<div class="might-grid">
												<div class="grid-might">
													<a href="single.php"><img src="images/c-10.jpg" class="img-responsive" alt=""> </a>
												</div>
												<div class="might-top">
													<h4><a href="single.php">Duis consectetur gravida</a></h4>
													<p> Nullam non magna lobortis, faucibus erat eu, consequat justo. Suspendisse commodo nibh odio.</p>
												</div>
												<div class="clearfix"></div>
											</div>
											<div class="might-grid">
												<div class="grid-might">
													<a href="single.php"><img src="images/c-11.jpg" class="img-responsive" alt=""> </a>
												</div>
												<div class="might-top">
													<h4><a href="single.php">Duis consectetur gravida</a></h4>
													<p> Nullam non magna lobortis, faucibus erat eu, consequat justo. Suspendisse commodo nibh odio.</p>
												</div>
												<div class="clearfix"></div>
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

									<div class="clearfix"> </div>
								</div>
							</div>
						</div>
						<!--slide-end-->
						<?php include_once("footer.php"); ?>
							<?php include ("script.php"); ?>

								<!-- all script -->

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
								<script type="application/x-javascript">
									addEventListener("load", function () {
										setTimeout(hideURLbar, 0);
									}, false);

									function hideURLbar() {
										window.scrollTo(0, 1);
									}
								</script>
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
								<!-- script-for-menu -->
								<!-- script-for-menu -->
								<script>
									$("span.menu").click(function () {
										$(" ul.navig").slideToggle("slow", function () {});
									});
								</script>
								<!-- script-for-menu -->
								<!-- all script -->
		</body>

	</html>